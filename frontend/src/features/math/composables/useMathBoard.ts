// useMathBoard: instant feedback while the player builds a step. The server replays and checks
// every step again, so nothing here decides what is saved or scored.
import { computed, ref, toValue, watch, type MaybeRefOrGetter } from 'vue'

import type { Operator, PlayedStep, StepInput } from '../types'

export interface Tile {
  id: string
  value: number
  /** A number the player computed, rather than one of the 6 starting numbers. */
  computed: boolean
}

/** The steps the browser can refuse at once, with the server's reason codes. */
export type RefusalReason = 'not_positive' | 'not_whole'

export interface Refusal {
  reason: RefusalReason
  step: StepInput
  tileId: string
}

/**
 * The numbers on the board after the saved steps: the unused starting numbers in their order,
 * then the computed ones. When a value is both, the starting copy is used up first, as the
 * server does, so the right tiles keep their "new" badge.
 */
export function boardTiles(numbers: number[], steps: PlayedStep[]): Tile[] {
  const starting: Tile[] = numbers.map((value, index) => ({
    id: `n${index}`,
    value,
    computed: false,
  }))
  const produced: Tile[] = []
  const take = (value: number) => {
    const pool = starting.some((tile) => tile.value === value) ? starting : produced
    const index = pool.findIndex((tile) => tile.value === value)
    if (index >= 0) pool.splice(index, 1)
  }
  steps.forEach((step, index) => {
    take(step.left)
    take(step.right)
    produced.push({ id: `s${index}`, value: step.result, computed: true })
  })
  return [...starting, ...produced]
}

/** Why a step can't be played, or null. The result must stay a positive whole number. */
export function checkStep({ left, op, right }: StepInput): RefusalReason | null {
  if (op === '-' && left <= right) return 'not_positive'
  if (op === '/' && left % right !== 0) return 'not_whole'
  return null
}

interface Options {
  numbers: MaybeRefOrGetter<number[]>
  steps: MaybeRefOrGetter<PlayedStep[]>
  disabled: MaybeRefOrGetter<boolean>
  /** Called with a step the browser accepted; the caller sends it to the server. */
  onStep: (step: StepInput) => void
}

/** Tap a number, then an operator, then a second number. Tapping a picked number unpicks it. */
export function useMathBoard({ numbers, steps, disabled, onStep }: Options) {
  const tiles = computed(() => boardTiles(toValue(numbers), toValue(steps)))
  const firstId = ref<string | null>(null)
  const operator = ref<Operator | null>(null)
  const refusal = ref<Refusal | null>(null)

  const first = computed(() => tiles.value.find((tile) => tile.id === firstId.value) ?? null)

  function clear() {
    firstId.value = null
    operator.value = null
  }

  // A save, an undo or a refresh changes the board, so a picked tile may be gone.
  watch(tiles, () => {
    clear()
    refusal.value = null
  })

  function selectTile(id: string) {
    const tile = tiles.value.find((candidate) => candidate.id === id)
    if (toValue(disabled) || !tile) return
    refusal.value = null
    if (first.value === null || operator.value === null || first.value.id === id) {
      if (first.value?.id === id) clear()
      else firstId.value = id
      return
    }
    const step = { left: first.value.value, op: operator.value, right: tile.value }
    const reason = checkStep(step)
    if (reason) {
      refusal.value = { reason, step, tileId: id }
      return
    }
    // The picks stay until the saved board comes back (the tiles watcher clears them then), so
    // after a failed save the player only has to tap the second number again.
    onStep(step)
  }

  function selectOperator(op: Operator) {
    if (toValue(disabled) || first.value === null) return
    refusal.value = null
    operator.value = operator.value === op ? null : op
  }

  return { tiles, firstId, operator, refusal, selectTile, selectOperator, clear }
}
