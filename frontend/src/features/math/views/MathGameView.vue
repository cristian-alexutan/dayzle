<!-- MathGameView: the daily Math game inside the shared game frame. -->
<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import AppButton from '@/shared/components/AppButton.vue'
import AppMessage from '@/shared/components/AppMessage.vue'
import AppSpinner from '@/shared/components/AppSpinner.vue'
import ErrorState from '@/shared/components/ErrorState.vue'
import GameShell from '@/shared/components/GameShell.vue'
import { formatGameDay } from '@/shared/utils/formatGameDay'

import {
  errorCode,
  useMathGameQuery,
  useMathHeartbeat,
  useSaveProgressMutation,
  useSubmitMutation,
} from '../api/queries'
import FloatingPi from '../components/FloatingPi.vue'
import GlitchOverlay from '../components/GlitchOverlay.vue'
import JugglingHands from '../components/JugglingHands.vue'
import MathResult from '../components/MathResult.vue'
import MathTarget from '../components/MathTarget.vue'
import NumberTile from '../components/NumberTile.vue'
import OperatorPicker from '../components/OperatorPicker.vue'
import StepHistory from '../components/StepHistory.vue'
import { useEasterEggs } from '../composables/useEasterEggs'
import { closestSoFar, useMathBoard } from '../composables/useMathBoard'
import { OPERATOR_SYMBOLS, type StepInput } from '../types'

const DAY = 'today'
const SHAKE_MS = 400

const { t, locale } = useI18n()

const query = useMathGameQuery(DAY)
const save = useSaveProgressMutation(DAY)
const submit = useSubmitMutation(DAY)

const game = computed(() => query.data.value)
const inProgress = computed(() => game.value?.status === 'in_progress')
const finished = computed(() => game.value?.status === 'completed')
const noPuzzle = computed(() => errorCode(query.error.value) === 'no_puzzle')
const boardDisabled = computed(
  () => !inProgress.value || save.isPending.value || submit.isPending.value,
)

useMathHeartbeat(DAY, inProgress)

const steps = computed(() => game.value?.steps ?? [])

const { tiles, firstId, operator, refusal, selectTile, selectOperator } = useMathBoard({
  numbers: () => game.value?.numbers ?? [],
  steps,
  disabled: boardDisabled,
  onStep: (step: StepInput) => saveSteps([...steps.value, step]),
})

/** Only while playing: once the game ends, the result shows the final number instead. */
const closestText = computed(() => {
  const closest =
    game.value && inProgress.value ? closestSoFar(tiles.value, game.value.target) : null
  return closest === null ? '' : t('math.closest', { value: closest })
})
/** Undo, reset and finish all need at least one step, and nothing else on its way. */
const canChange = computed(() => !boardDisabled.value && steps.value.length > 0)

/** Shown when the server refuses a step the browser accepted, e.g. after a change elsewhere. */
const serverError = ref<string | null>(null)

/**
 * After a refused save or finish the board is reloaded, so the next action builds on the
 * server's steps rather than on a stale copy (another tab, or a page left open past midnight).
 * Finished in another tab: the reload shows that game instead of an error.
 */
function onRefused(error: Error, refusedMessage: string) {
  const code = errorCode(error)
  if (code !== 'already_played')
    serverError.value = t(code === 'invalid_step' ? refusedMessage : 'math.errors.generic')
  query.refetch()
}

const eggs = useEasterEggs()

/**
 * How many steps the board will have once a new step is saved, or null. Only that step can play
 * an easter egg: steps restored on load, an undo or a reset never do.
 */
let awaitedSteps: number | null = null

/**
 * A step, an undo and a reset all save the whole list of steps: the server replays it from the
 * starting numbers and sends the board back.
 */
function saveSteps(next: StepInput[]) {
  serverError.value = null
  awaitedSteps = next.length > steps.value.length ? next.length : null
  save.mutate(next, {
    onError: (error) => {
      awaitedSteps = null
      onRefused(error, 'math.refused.server')
    },
  })
}

watch(steps, (now) => {
  const step = now[now.length - 1]
  if (step && now.length === awaitedSteps) eggs.celebrate(step)
  awaitedSteps = null
})

/** End the game with the computed number closest to the target; the server picks and scores it. */
function finish() {
  serverError.value = null
  submit.mutate(steps.value, { onError: (error) => onRefused(error, 'math.errors.finish') })
}

const message = computed(() => {
  if (refusal.value) {
    const { left, op, right } = refusal.value.step
    const step = `${left} ${OPERATOR_SYMBOLS[op]} ${right}`
    return t(`math.refused.${refusal.value.reason}`, { step })
  }
  return serverError.value
})

// Picking a new number starts a new try. A reload that clears the picks keeps the message.
watch(firstId, (id) => {
  if (id !== null) serverError.value = null
})

/** The refused tile and a count that grows with each refusal, so every refusal shakes again. */
const shake = ref<{ tileId: string; count: number } | null>(null)
let shakeCount = 0
let shakeTimer: ReturnType<typeof setTimeout> | undefined
watch(refusal, (current) => {
  if (!current) return
  shakeCount += 1
  shake.value = { tileId: current.tileId, count: shakeCount }
  clearTimeout(shakeTimer)
  shakeTimer = setTimeout(() => (shake.value = null), SHAKE_MS)
})

/** "Puzzle-ul zilei · sâmbătă, 7 noiembrie": the puzzle's day, in the player's language. */
const subtitle = computed(() =>
  game.value ? t('math.subtitle', { date: formatGameDay(game.value.date, locale.value) }) : '',
)

// The result opens by itself when the game ends, or right away when a finished game loads.
// The step that ends the game may also play an easter egg: the result waits for it to finish.
const resultVisible = ref(false)
let resultTimer: ReturnType<typeof setTimeout> | undefined
let stopWaitingForEgg: (() => void) | undefined
watch(
  finished,
  (isFinished) => {
    if (!isFinished) return
    // One tick later, so the finishing step's egg (started by the steps watcher) is known.
    resultTimer = setTimeout(() => {
      if (eggs.active.value === null) {
        resultVisible.value = true
        return
      }
      stopWaitingForEgg = watch(eggs.active, (egg) => {
        if (egg !== null) return
        stopWaitingForEgg?.()
        resultVisible.value = true
      })
    }, 0)
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  clearTimeout(shakeTimer)
  clearTimeout(resultTimer)
  stopWaitingForEgg?.()
})
</script>

<template>
  <GameShell :title="t('math.title')">
    <AppSpinner v-if="query.isPending.value" :aria-label="t('math.loading')" />
    <AppMessage v-else-if="noPuzzle" severity="info" data-test="no-puzzle">
      {{ t('math.noPuzzle') }}
    </AppMessage>
    <ErrorState
      v-else-if="query.isError.value"
      :message="t('math.errors.generic')"
      retryable
      @retry="query.refetch()"
    />
    <template v-else-if="game">
      <p class="math-game__subtitle" data-test="subtitle">{{ subtitle }}</p>
      <MathTarget :target="game.target" />
      <div class="math-game__board" data-test="board">
        <div
          class="math-game__tiles"
          :class="{ 'math-game__tiles--glitch': eggs.active.value === 'glitch' }"
          role="group"
          :aria-label="t('math.numbers')"
        >
          <NumberTile
            v-for="tile in tiles"
            :key="tile.id"
            :tile="tile"
            :selected="firstId === tile.id"
            :refused="refusal?.tileId === tile.id"
            :shake="shake?.tileId === tile.id ? shake.count : 0"
            :disabled="boardDisabled"
            @select="selectTile(tile.id)"
          />
        </div>
        <OperatorPicker
          :selected="operator"
          :disabled="boardDisabled"
          :juggling="eggs.active.value === 'operators'"
          @choose="selectOperator"
        />
        <JugglingHands v-if="eggs.active.value === 'hands'" data-test="egg-hands" />
        <GlitchOverlay v-if="eggs.active.value === 'glitch'" data-test="egg-glitch" />
        <FloatingPi v-if="eggs.active.value === 'pi'" data-test="egg-pi" />
      </div>
      <p v-if="message" class="math-game__refusal" role="alert" data-test="refusal">
        <i class="pi pi-exclamation-circle" aria-hidden="true" />
        <span>{{ message }}</span>
      </p>
      <p v-if="closestText" class="math-game__closest" aria-hidden="true" data-test="closest">
        {{ closestText }}
      </p>
      <!-- Always in the page, so screen readers announce every change of the closest number. -->
      <p class="math-game__announce" aria-live="polite" data-test="closest-announce">
        {{ closestText }}
      </p>
      <StepHistory :steps="steps" :max-steps="game.max_steps" />
      <div v-if="inProgress" class="math-game__controls">
        <AppButton
          :label="t('math.undo')"
          icon="pi pi-undo"
          severity="secondary"
          outlined
          :disabled="!canChange"
          data-test="undo"
          @click="saveSteps(steps.slice(0, -1))"
        />
        <AppButton
          :label="t('math.reset')"
          icon="pi pi-refresh"
          severity="secondary"
          text
          :disabled="!canChange"
          data-test="reset"
          @click="saveSteps([])"
        />
        <AppButton
          class="math-game__finish"
          :label="t('math.finish')"
          icon="pi pi-flag"
          :disabled="!canChange"
          data-test="finish"
          @click="finish"
        />
      </div>
      <AppButton
        v-if="finished && !resultVisible"
        class="math-game__see-result"
        :label="t('math.result.see')"
        icon="pi pi-trophy"
        rounded
        raised
        data-test="see-result"
        @click="resultVisible = true"
      />
      <MathResult v-if="finished" v-model:visible="resultVisible" :game="game" />
    </template>
  </GameShell>
</template>

<style scoped>
.math-game__subtitle {
  margin: -0.5rem 0 0;
  color: var(--dz-text-muted);
  font-size: 0.875rem;
}

/* The tiles and operators, with room for an easter egg on top of them. */
.math-game__board {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  width: 100%;
}

.math-game__tiles {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
  width: 100%;
}

/* The 404 easter egg: the tiles jump sideways, a few pixels at a time. */
.math-game__tiles--glitch {
  animation: math-game-glitch 0.4s steps(1, end) 4;
}

@keyframes math-game-glitch {
  0% {
    transform: translateX(8px);
  }
  25% {
    transform: translateX(-12px);
  }
  50% {
    transform: translateX(6px);
  }
  75% {
    transform: translateX(-10px);
  }
  100% {
    transform: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .math-game__tiles--glitch {
    animation: none;
  }
}

.math-game__closest {
  margin: 0;
  font-weight: 700;
}

.math-game__controls {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  width: 100%;
}

.math-game__finish {
  grid-column: 1 / -1;
}

.math-game__see-result {
  align-self: center;
}

/* Read by screen readers, hidden on screen (the visible line above shows the same text). */
.math-game__announce {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
  border: 0;
}

.math-game__refusal {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  width: 100%;
  margin: 0;
  color: var(--dz-accent-strong);
  font-size: 0.95rem;
  font-weight: 600;
}
</style>
