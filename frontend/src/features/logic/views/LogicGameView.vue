<!-- LogicGameView: the daily Logic game (Sunspots) inside the shared game frame. -->
<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import AppButton from '@/shared/components/AppButton.vue'
import AppMessage from '@/shared/components/AppMessage.vue'
import AppSpinner from '@/shared/components/AppSpinner.vue'
import ErrorState from '@/shared/components/ErrorState.vue'
import GameShell from '@/shared/components/GameShell.vue'

import {
  errorCode,
  useLogicGameQuery,
  useLogicHeartbeat,
  useMarksMutation,
  usePlaceMutation,
} from '../api/queries'
import LogicBoard from '../components/LogicBoard.vue'
import LogicResult from '../components/LogicResult.vue'
import LogicToolbar from '../components/LogicToolbar.vue'
import LogicTutorial from '../components/LogicTutorial.vue'
import { useBoardState } from '../composables/useBoardState'
import { useConflicts, WRONG_SUN_MS } from '../composables/useConflicts'
import { useElapsedTime } from '../composables/useElapsedTime'
import type { Cell } from '../types'

const DAY = 'today'
const ERROR_MS = 2500
const TUTORIAL_SEEN_KEY = 'dayzle.logic.tutorialSeen'

const { t } = useI18n()

const query = useLogicGameQuery(DAY)
const placeSun = usePlaceMutation(DAY)
const saveMarks = useMarksMutation(DAY)

const game = computed(() => query.data.value)
const inProgress = computed(() => game.value?.status === 'in_progress')
const finished = computed(() => game.value?.status === 'completed')
const noPuzzle = computed(() => errorCode(query.error.value) === 'no_puzzle')

useLogicHeartbeat(DAY, inProgress)

const elapsedMs = useElapsedTime(() => game.value?.elapsed_ms ?? 0, inProgress)
const conflicts = useConflicts()
const errorMessage = ref<string | null>(null)
let errorTimer: ReturnType<typeof setTimeout> | undefined

function showError(message: string) {
  errorMessage.value = message
  clearTimeout(errorTimer)
  errorTimer = setTimeout(() => (errorMessage.value = null), ERROR_MS)
}

function place(cell: Cell) {
  placeSun.mutate(cell, {
    onSuccess: (result) => {
      if (!result.correct) conflicts.show(cell, result.conflicts)
    },
    onError: (error) => {
      // Finished in another tab: show that game instead of an error.
      if (errorCode(error) === 'already_played') query.refetch()
      else showError(t('logic.errors.generic'))
    },
  })
}

const board = useBoardState({
  game,
  disabled: () => !inProgress.value || placeSun.isPending.value,
  place,
  // A failed save is ignored: the next tap sends all the marks again.
  saveMarks: (marks) => {
    if (inProgress.value) saveMarks.mutate(marks)
  },
})

const tutorialVisible = ref(false)

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

// The rules open by themselves the first time a player starts a game.
watch(
  () => game.value?.status,
  (status) => {
    if (status !== 'in_progress' || tutorialSeen()) return
    tutorialVisible.value = true
    rememberTutorialSeen()
  },
  { immediate: true },
)

const resultVisible = ref(false)
let resultTimer: ReturnType<typeof setTimeout> | undefined

// The result opens by itself: right away when a finished game loads, a moment after the last
// sun when the player has just finished it.
watch(
  () => game.value?.status,
  (status, previous) => {
    if (status !== 'completed') return
    if (previous !== 'in_progress') resultVisible.value = true
    else resultTimer = setTimeout(() => (resultVisible.value = true), WRONG_SUN_MS)
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
        :streak="game.streak"
        :can-undo="board.canUndo.value"
        :has-marks="board.hasMarks.value"
        :playing="inProgress"
        @undo="board.undoMark"
        @clear="board.clearMarks"
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
        :is-wrong="conflicts.isWrong"
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
      <LogicTutorial v-model:visible="tutorialVisible" />
    </template>
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
