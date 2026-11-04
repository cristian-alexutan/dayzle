<!-- WordGameView: the daily Word game inside the shared game frame. -->
<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import AppMessage from '@/shared/components/AppMessage.vue'
import AppSpinner from '@/shared/components/AppSpinner.vue'
import ErrorState from '@/shared/components/ErrorState.vue'
import GameShell from '@/shared/components/GameShell.vue'

import { errorCode, useGuessMutation, useWordGameQuery, useWordHeartbeat } from '../api/queries'
import WordBoard from '../components/WordBoard.vue'
import WordKeyboard from '../components/WordKeyboard.vue'
import { useGuessInput } from '../composables/useGuessInput'
import { useKeyboardState } from '../composables/useKeyboardState'
import '../word.css'

const DAY = 'today'
const REJECTION_MS = 2000
const SHAKE_MS = 400

const { t } = useI18n()

const query = useWordGameQuery(DAY)
const guess = useGuessMutation(DAY)

const game = computed(() => query.data.value)
const guesses = computed(() => game.value?.guesses ?? [])
const inProgress = computed(() => game.value?.status === 'in_progress')

const noPuzzle = computed(() => errorCode(query.error.value) === 'no_puzzle')

useWordHeartbeat(DAY, inProgress)

const input = useGuessInput({
  length: () => game.value?.word_length ?? 0,
  disabled: () => !inProgress.value || guess.isPending.value,
  onSubmit: submit,
})
const keyColors = useKeyboardState(guesses)

const revealRow = ref<number | null>(null)
const rejection = ref<string | null>(null)
const shake = ref(false)
let rejectionTimer: ReturnType<typeof setTimeout> | undefined
let shakeTimer: ReturnType<typeof setTimeout> | undefined

function reject(message: string) {
  rejection.value = message
  shake.value = true
  clearTimeout(rejectionTimer)
  clearTimeout(shakeTimer)
  rejectionTimer = setTimeout(() => (rejection.value = null), REJECTION_MS)
  shakeTimer = setTimeout(() => (shake.value = false), SHAKE_MS)
}

function submit() {
  if (!input.isComplete.value) {
    reject(t('word.errors.tooShort'))
    return
  }
  guess.mutate(input.text.value, {
    onSuccess: (updated) => {
      revealRow.value = updated.guesses.length - 1
      input.clear()
    },
    onError: (error) => {
      const code = errorCode(error)
      // Finished in another tab: show that game instead of an error.
      if (code === 'already_played') query.refetch()
      else if (code === 'not_a_word' || code === 'invalid') reject(t(`word.errors.${code}`))
      else reject(t('word.errors.generic'))
    },
  })
}

onBeforeUnmount(() => {
  clearTimeout(rejectionTimer)
  clearTimeout(shakeTimer)
})
</script>

<template>
  <GameShell :title="t('word.title')">
    <AppSpinner v-if="query.isPending.value" :aria-label="t('word.loading')" />
    <AppMessage v-else-if="noPuzzle" severity="info" data-test="no-puzzle">
      {{ t('word.noPuzzle') }}
    </AppMessage>
    <ErrorState
      v-else-if="query.isError.value"
      :message="t('word.errors.generic')"
      retryable
      @retry="query.refetch()"
    />
    <template v-else-if="game">
      <div class="word-game__message" aria-live="polite">
        <AppMessage v-if="rejection" severity="warn" size="small" data-test="rejection">
          {{ rejection }}
        </AppMessage>
      </div>
      <WordBoard
        :guesses="guesses"
        :current="input.letters.value"
        :rows="game.max_attempts"
        :length="game.word_length"
        :reveal-row="revealRow"
        :shake="shake"
      />
      <WordKeyboard
        v-if="inProgress"
        :colors="keyColors"
        :disabled="guess.isPending.value"
        @letter="input.addLetter"
        @enter="input.submit"
        @backspace="input.removeLetter"
      />
    </template>
  </GameShell>
</template>

<style scoped>
.word-game__message {
  display: flex;
  align-items: center;
  min-height: 2.5rem;
}
</style>
