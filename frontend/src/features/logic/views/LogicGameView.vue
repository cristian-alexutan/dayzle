<!-- LogicGameView: the daily Logic game (Sunspots) inside the shared game frame. -->
<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import AppButton from '@/shared/components/AppButton.vue'
import AppMessage from '@/shared/components/AppMessage.vue'
import AppSpinner from '@/shared/components/AppSpinner.vue'
import ErrorState from '@/shared/components/ErrorState.vue'
import GameShell from '@/shared/components/GameShell.vue'
import { useTimer } from '@/shared/composables/useTimer'

import {
  errorCode,
  useCellMutation,
  useClearMutation,
  useLogicGameQuery,
  useLogicHeartbeat,
} from '../api/queries'
import LogicBoard from '../components/LogicBoard.vue'
import LogicResult from '../components/LogicResult.vue'
import LogicToolbar from '../components/LogicToolbar.vue'
import LogicTutorial from '../components/LogicTutorial.vue'
import { useBoardState } from '../composables/useBoardState'
import { useConflicts } from '../composables/useConflicts'

const DAY = 'today'
const ERROR_MS = 2500
/** A moment to see the last sun on the board before the result opens. */
const RESULT_DELAY_MS = 600
const TUTORIAL_SEEN_KEY = 'dayzle.logic.tutorialSeen'

const { t } = useI18n()

function tutorialSeen(): boolean {
  try {
    return localStorage.getItem(TUTORIAL_SEEN_KEY) === 'yes'
  } catch {
    return true
  }
}

function rememberTutorialSeen() {
  try {
    localStorage.setItem(TUTORIAL_SEEN_KEY, 'yes')
  } catch {
    // Not remembered, e.g. in a private window: the tutorial just opens again next time.
  }
}

// The first time, the rules open before the game is loaded: loading it starts the clock, so
// reading them doesn't count as play time.
const started = ref(tutorialSeen())
const tutorialVisible = ref(!started.value)

watch(tutorialVisible, (visible) => {
  if (visible || started.value) return
  started.value = true
  rememberTutorialSeen()
})

const query = useLogicGameQuery(DAY, started)
const game = computed(() => query.data.value)
const inProgress = computed(() => game.value?.status === 'in_progress')
const finished = computed(() => game.value?.status === 'completed')
const noPuzzle = computed(() => errorCode(query.error.value) === 'no_puzzle')
// Reading the rules again in the middle of a game pauses the clock too.
const playing = computed(() => inProgress.value && !tutorialVisible.value)

useLogicHeartbeat(DAY, playing)
const elapsedMs = useTimer(() => game.value?.elapsed_ms ?? 0, playing)

const conflicts = useConflicts()
const errorMessage = ref<string | null>(null)
let errorTimer: ReturnType<typeof setTimeout> | undefined

function onError(error: unknown) {
  // Finished in another tab: the board is loaded again and shows that game.
  if (errorCode(error) === 'already_played') return
  errorMessage.value = t('logic.errors.generic')
  clearTimeout(errorTimer)
  errorTimer = setTimeout(() => (errorMessage.value = null), ERROR_MS)
}

const cellMutation = useCellMutation(DAY, {
  onRejected: (cell, conflicting) => {
    board.forget(cell)
    conflicts.show(cell, conflicting)
  },
  onError,
})
const clearMutation = useClearMutation(DAY, { onError })

const board = useBoardState({
  game,
  disabled: () => !inProgress.value,
  change: (change) => cellMutation.mutate(change),
})

function clearBoard() {
  board.clearHistory()
  clearMutation.mutate()
}

const resultVisible = ref(false)
let resultTimer: ReturnType<typeof setTimeout> | undefined

// The result opens by itself: right away when a finished game loads, a moment after the last
// sun when the player has just finished it.
watch(
  () => game.value?.status,
  (status, previous) => {
    if (status !== 'completed') return
    if (previous !== 'in_progress') resultVisible.value = true
    else resultTimer = setTimeout(() => (resultVisible.value = true), RESULT_DELAY_MS)
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  clearTimeout(errorTimer)
  clearTimeout(resultTimer)
})
</script>

<template>
  <GameShell :title="t('logic.title')">
    <AppSpinner v-if="query.isPending.value" :aria-label="t('logic.loading')" />
    <AppMessage v-else-if="noPuzzle" severity="info" data-test="no-puzzle">
      {{ t('logic.noPuzzle') }}
    </AppMessage>
    <ErrorState
      v-else-if="query.isError.value"
      :message="t('logic.errors.generic')"
      retryable
      @retry="query.refetch()"
    />
    <template v-else-if="game">
      <LogicToolbar
        :elapsed-ms="elapsedMs"
        :mistakes="game.mistakes"
        :can-undo="board.canUndo.value"
        :can-clear="!board.isEmpty.value"
        :playing="inProgress"
        @undo="board.undo"
        @clear="clearBoard"
        @help="tutorialVisible = true"
      />
      <div class="logic-game__message" aria-live="polite">
        <AppMessage v-if="errorMessage" severity="error" size="small" data-test="error">
          {{ errorMessage }}
        </AppMessage>
      </div>
      <LogicBoard
        :regions="game.regions"
        :content-of="board.contentOf"
        :is-rejected="conflicts.isRejected"
        :is-conflict="conflicts.isConflict"
        :disabled="!inProgress"
        @tap="board.tap"
      />
      <template v-if="finished">
        <AppButton
          v-if="!resultVisible"
          class="logic-game__see-result"
          :label="t('logic.result.see')"
          icon="pi pi-trophy"
          rounded
          raised
          data-test="see-result"
          @click="resultVisible = true"
        />
        <LogicResult v-model:visible="resultVisible" :game="game" />
      </template>
    </template>
    <LogicTutorial v-model:visible="tutorialVisible" />
  </GameShell>
</template>

<style scoped>
/* Space kept for the message, so the board doesn't move when one appears. */
.logic-game__message {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 1.75rem;
  margin-block: -0.5rem;
}

.logic-game__see-result {
  padding-inline: 1.5rem;
  font-weight: 600;
}
</style>
