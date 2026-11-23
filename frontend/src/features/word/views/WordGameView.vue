<!-- WordGameView: the daily Word game inside the shared game frame. -->
<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import AppButton from '@/shared/components/AppButton.vue'
import AppMessage from '@/shared/components/AppMessage.vue'
import AppSpinner from '@/shared/components/AppSpinner.vue'
import ErrorState from '@/shared/components/ErrorState.vue'
import GameActionButton from '@/shared/components/GameActionButton.vue'
import GameShell from '@/shared/components/GameShell.vue'
import HowToPlay from '@/shared/components/HowToPlay.vue'

import {
  errorCode,
  useGuessMutation,
  useHintMutation,
  useWordGameQuery,
  useWordHeartbeat,
} from '../api/queries'
import WordBoard from '../components/WordBoard.vue'
import WordKeyboard from '../components/WordKeyboard.vue'
import WordResult from '../components/WordResult.vue'
import WordTile from '../components/WordTile.vue'
import { useGuessInput } from '../composables/useGuessInput'
import { useKeyboardState } from '../composables/useKeyboardState'

const DAY = 'today'
const REJECTION_MS = 2000
const NOTICE_MS = 3000
const SHAKE_MS = 400
/** Long enough for the last tile of a 5-letter row to finish flipping. */
const REVEAL_MS = 1500

const { t } = useI18n()

const query = useWordGameQuery(DAY)
const guess = useGuessMutation(DAY)
const hint = useHintMutation(DAY)

const game = computed(() => query.data.value)
const guesses = computed(() => game.value?.guesses ?? [])
const hints = computed(() => game.value?.hints ?? [])
const inProgress = computed(() => game.value?.status === 'in_progress')
const finished = computed(() => game.value?.status === 'completed')

const rulesSections = computed(() => [
  {
    heading: t('common.howToPlay.rulesHeading'),
    rules: [
      { icon: 'pi pi-pencil', text: t('word.rules.guess') },
      { icon: 'pi pi-palette', text: t('word.rules.colors') },
    ],
  },
  {
    heading: t('common.howToPlay.scoringHeading'),
    rules: [
      { icon: 'pi pi-star', text: t('word.rules.score') },
      {
        icon: 'pi pi-lightbulb',
        text: t('word.rules.hint', { points: game.value?.hint_penalty }),
      },
    ],
  },
])

const noPuzzle = computed(() => errorCode(query.error.value) === 'no_puzzle')

// Every visit to an unfinished game starts with the rules; a finished one shows only its
// result. Decided once, when the game loads, so finishing it doesn't open them again.
const rulesVisible = ref(false)
let rulesDecided = false
watch(
  () => game.value?.status,
  (status) => {
    if (rulesDecided || status === undefined) return
    rulesDecided = true
    rulesVisible.value = status === 'in_progress'
  },
  { immediate: true },
)

// The clock doesn't run while the rules are open.
useWordHeartbeat(DAY, () => inProgress.value && !rulesVisible.value)

const input = useGuessInput({
  length: () => game.value?.word_length ?? 0,
  disabled: () =>
    !inProgress.value || guess.isPending.value || hint.isPending.value || rulesVisible.value,
  onSubmit: submit,
})
const keyColors = useKeyboardState(guesses, hints)

const revealRow = ref<number | null>(null)
const rejection = ref<string | null>(null)
const shake = ref(false)
let rejectionTimer: ReturnType<typeof setTimeout> | undefined
let shakeTimer: ReturnType<typeof setTimeout> | undefined

/** A friendly message, such as when a hint has nothing left to reveal. */
const notice = ref<string | null>(null)
let noticeTimer: ReturnType<typeof setTimeout> | undefined

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

function showNotice(message: string) {
  notice.value = message
  clearTimeout(noticeTimer)
  noticeTimer = setTimeout(() => (notice.value = null), NOTICE_MS)
}

function takeHint() {
  hint.mutate(undefined, {
    onError: (error) => {
      const code = errorCode(error)
      if (code === 'nothing_to_hint') showNotice(t('word.hint.nothingLeft'))
      else if (code === 'already_played') query.refetch()
      else reject(t('word.errors.generic'))
    },
  })
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
  clearTimeout(noticeTimer)
  clearTimeout(resultTimer)
})
</script>

<template>
  <GameShell :title="t('word.title')">
    <template #actions>
      <GameActionButton
        v-if="inProgress"
        :label="t('word.hint.label')"
        icon="pi pi-lightbulb"
        :loading="hint.isPending.value"
        :disabled="guess.isPending.value"
        data-test="hint"
        @click="takeHint"
      />
      <HowToPlay v-model:visible="rulesVisible" :sections="rulesSections" />
    </template>
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
        <AppMessage v-if="rejection" severity="error" size="small" data-test="rejection">
          {{ rejection }}
        </AppMessage>
        <AppMessage v-else-if="notice" severity="info" size="small" data-test="hint-notice">
          {{ notice }}
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
      <div
        v-if="hints.length"
        class="word-game__hint-letters"
        :aria-label="t('word.hint.revealed', { letters: hints.join(', ') })"
        data-test="hint-letters"
      >
        <WordTile
          v-for="(letter, index) in hints"
          :key="index"
          class="word-game__hint-tile"
          :letter="letter"
          color="present"
          aria-hidden="true"
        />
      </div>
      <WordKeyboard
        v-if="inProgress"
        :colors="keyColors"
        :disabled="guess.isPending.value || hint.isPending.value"
        @letter="input.addLetter"
        @enter="input.submit"
        @backspace="input.removeLetter"
      />
      <template v-if="finished">
        <AppButton
          v-if="!resultVisible"
          class="word-game__see-result"
          :label="t('word.result.see')"
          icon="pi pi-trophy"
          rounded
          raised
          data-test="see-result"
          @click="resultVisible = true"
        />
        <WordResult v-model:visible="resultVisible" :game="game" />
      </template>
    </template>
  </GameShell>
</template>

<style scoped>
/* Space kept for the message, so the board doesn't move when one appears. */
.word-game__message {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 1.75rem;
  margin-block: -0.5rem;
}

.word-game__hint-letters {
  display: flex;
  gap: 0.35rem;
}

.word-game__hint-tile {
  width: 2rem;
  font-size: 1rem;
}

.word-game__see-result {
  padding-inline: 1.5rem;
  font-weight: 600;
}
</style>
