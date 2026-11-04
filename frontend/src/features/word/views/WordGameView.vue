<!-- WordGameView: the daily Word game inside the shared game frame. -->
<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import AppButton from '@/shared/components/AppButton.vue'
import AppMessage from '@/shared/components/AppMessage.vue'
import AppSpinner from '@/shared/components/AppSpinner.vue'
import ErrorState from '@/shared/components/ErrorState.vue'
import GameShell from '@/shared/components/GameShell.vue'

import { errorCode, useGuessMutation, useWordGameQuery, useWordHeartbeat } from '../api/queries'
import WordBoard from '../components/WordBoard.vue'
import WordKeyboard from '../components/WordKeyboard.vue'
import WordResult from '../components/WordResult.vue'
import { useGuessInput } from '../composables/useGuessInput'
import { useKeyboardState } from '../composables/useKeyboardState'
import '../word.css'

const DAY = 'today'
const REJECTION_MS = 2000
const SHAKE_MS = 400
/** Long enough for the last tile of a 5-letter row to finish flipping. */
const REVEAL_MS = 1500

const { t } = useI18n()

const query = useWordGameQuery(DAY)
const guess = useGuessMutation(DAY)

const game = computed(() => query.data.value)
const guesses = computed(() => game.value?.guesses ?? [])
const inProgress = computed(() => game.value?.status === 'in_progress')
const finished = computed(() => game.value?.status === 'completed')

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

const resultVisible = ref(false)
let resultTimer: ReturnType<typeof setTimeout> | undefined

// The result opens by itself: right away when a finished game loads, after the flip when the
// player has just finished it.
watch(
  finished,
  (isFinished) => {
    if (!isFinished) return
    resultTimer = setTimeout(
      () => (resultVisible.value = true),
      revealRow.value === null ? 0 : REVEAL_MS,
    )
  },
  { immediate: true },
)

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
  revealRow.value = guesses.value.length
  guess.mutate(input.text.value, {
    onSuccess: () => input.clear(),
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
  clearTimeout(resultTimer)
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
      <template v-if="finished">
        <AppButton
          v-if="!resultVisible"
          :label="t('word.result.see')"
          data-test="see-result"
          @click="resultVisible = true"
        />
        <WordResult v-model:visible="resultVisible" :game="game" />
      </template>
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
