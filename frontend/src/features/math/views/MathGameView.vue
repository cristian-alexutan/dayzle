<!-- MathGameView: the daily Math game inside the shared game frame. -->
<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

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
import { useMathBoard } from '../composables/useMathBoard'
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

const { tiles, firstId, operator, refusal, selectTile, selectOperator } = useMathBoard({
  numbers: () => game.value?.numbers ?? [],
  steps: () => game.value?.steps ?? [],
  disabled: boardDisabled,
  onStep: play,
})

/** Shown when the server refuses a step the browser accepted, e.g. after a change elsewhere. */
const serverError = ref<string | null>(null)

/**
 * Every step goes to the server, which replays the whole board and sends it back. After a
 * refused save the board is reloaded, so the next step builds on the server's steps rather than
 * on a stale copy (another tab, or a page left open past midnight).
 */
function play(step: StepInput) {
  serverError.value = null
  save.mutate([...(game.value?.steps ?? []), step], {
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

const shakingId = ref<string | null>(null)
let shakeTimer: ReturnType<typeof setTimeout> | undefined
watch(refusal, (current) => {
  if (!current) return
  shakingId.value = current.tileId
  clearTimeout(shakeTimer)
  shakeTimer = setTimeout(() => (shakingId.value = null), SHAKE_MS)
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
          :shaking="shakingId === tile.id"
          :disabled="boardDisabled"
          @select="selectTile(tile.id)"
        />
      </div>
      <OperatorPicker :selected="operator" :disabled="boardDisabled" @choose="selectOperator" />
      <p v-if="message" class="math-game__refusal" role="alert" data-test="refusal">
        <i class="pi pi-exclamation-circle" aria-hidden="true" />
        <span>{{ message }}</span>
      </p>
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
