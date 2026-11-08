<!-- MathGameView: the daily Math game inside the shared game frame. -->
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
  useMathGameQuery,
  useMathHeartbeat,
  useSaveProgressMutation,
} from '../api/queries'
import MathTarget from '../components/MathTarget.vue'
import NumberTile from '../components/NumberTile.vue'
import OperatorPicker from '../components/OperatorPicker.vue'
import StepHistory from '../components/StepHistory.vue'
import { closestSoFar, useMathBoard } from '../composables/useMathBoard'
import { OPERATOR_SYMBOLS, type StepInput } from '../types'

const DAY = 'today'
const SHAKE_MS = 400

const { t, locale } = useI18n()

const query = useMathGameQuery(DAY)
const save = useSaveProgressMutation(DAY)

const game = computed(() => query.data.value)
const inProgress = computed(() => game.value?.status === 'in_progress')
const finished = computed(() => game.value?.status === 'completed')
const noPuzzle = computed(() => errorCode(query.error.value) === 'no_puzzle')
const boardDisabled = computed(() => !inProgress.value || save.isPending.value)

useMathHeartbeat(DAY, inProgress)

const steps = computed(() => game.value?.steps ?? [])

const { tiles, firstId, operator, refusal, selectTile, selectOperator } = useMathBoard({
  numbers: () => game.value?.numbers ?? [],
  steps,
  disabled: boardDisabled,
  onStep: (step: StepInput) => saveSteps([...steps.value, step]),
})

const closest = computed(() => (game.value ? closestSoFar(tiles.value, game.value.target) : null))
const canUndo = computed(() => !boardDisabled.value && steps.value.length > 0)

/** Shown when the server refuses a step the browser accepted, e.g. after a change elsewhere. */
const serverError = ref<string | null>(null)

/**
 * A step, an undo and a reset all save the whole list of steps: the server replays it from the
 * starting numbers and sends the board back. After a refused save the board is reloaded, so the
 * next step builds on the server's steps rather than on a stale copy (another tab, or a page
 * left open past midnight).
 */
function saveSteps(next: StepInput[]) {
  serverError.value = null
  save.mutate(next, {
    onError: (error) => {
      const code = errorCode(error)
      // Finished in another tab: the reload shows that game instead of an error.
      if (code !== 'already_played')
        serverError.value = t(
          code === 'invalid_step' ? 'math.refused.server' : 'math.errors.generic',
        )
      query.refetch()
    },
  })
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

/** "sâmbătă, 7 noiembrie": the puzzle's day, in the player's language. */
const subtitle = computed(() => {
  if (!game.value) return ''
  const [year, month, day] = game.value.date.split('-').map(Number) as [number, number, number]
  const date = new Intl.DateTimeFormat(locale.value, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  }).format(new Date(year, month - 1, day))
  return t('math.subtitle', { date })
})

onBeforeUnmount(() => clearTimeout(shakeTimer))
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
      <div class="math-game__tiles" role="group" :aria-label="t('math.numbers')">
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
      <OperatorPicker :selected="operator" :disabled="boardDisabled" @choose="selectOperator" />
      <p v-if="message" class="math-game__refusal" role="alert" data-test="refusal">
        <i class="pi pi-exclamation-circle" aria-hidden="true" />
        <span>{{ message }}</span>
      </p>
      <p v-if="closest !== null" class="math-game__closest" data-test="closest">
        {{ t('math.closest', { value: closest }) }}
      </p>
      <StepHistory :steps="steps" :max-steps="game.max_steps" />
      <div v-if="inProgress" class="math-game__controls">
        <AppButton
          :label="t('math.undo')"
          icon="pi pi-undo"
          severity="secondary"
          outlined
          :disabled="!canUndo"
          data-test="undo"
          @click="saveSteps(steps.slice(0, -1))"
        />
        <AppButton
          :label="t('math.reset')"
          icon="pi pi-refresh"
          severity="secondary"
          outlined
          :disabled="!canUndo"
          data-test="reset"
          @click="saveSteps([])"
        />
      </div>
      <AppMessage v-if="finished" severity="success" data-test="finished">
        {{ t('math.finished', { score: game.score }) }}
      </AppMessage>
    </template>
  </GameShell>
</template>

<style scoped>
.math-game__subtitle {
  margin: -0.5rem 0 0;
  color: var(--dz-text-muted);
  font-size: 0.875rem;
}

.math-game__tiles {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
  width: 100%;
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
