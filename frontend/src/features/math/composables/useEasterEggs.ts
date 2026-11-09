// useEasterEggs: small animations for special numbers. Cosmetic only: they never change what is
// saved or scored, and they only react to steps the server has just confirmed.
import { getCurrentScope, onScopeDispose, readonly, ref } from 'vue'

import type { PlayedStep } from '../types'

export type EasterEgg = 'hands' | 'operators' | 'glitch' | 'pi'

/** How long an easter egg stays on screen. */
export const EGG_MS = 1600

const RESULT_EGGS: Partial<Record<number, EasterEgg>> = { 67: 'hands', 404: 'glitch', 314: 'pi' }

/**
 * The easter egg a step triggers, or null: a result of 67 (juggling hands), 404 (the board
 * glitches) or 314 (a π floats by), or a step that uses a 6 and a 7 (the operators juggle).
 */
export function eggForStep({ left, right, result }: PlayedStep): EasterEgg | null {
  const byResult = RESULT_EGGS[result]
  if (byResult) return byResult
  if ((left === 6 && right === 7) || (left === 7 && right === 6)) return 'operators'
  return null
}

/** Plays each easter egg at most once per game, for `EGG_MS`. */
export function useEasterEggs() {
  const active = ref<EasterEgg | null>(null)
  const shown = new Set<EasterEgg>()
  let timer: ReturnType<typeof setTimeout> | undefined

  /** Call with a step the server has just saved (never with steps restored on load). */
  function celebrate(step: PlayedStep) {
    const egg = eggForStep(step)
    if (!egg || shown.has(egg)) return
    shown.add(egg)
    active.value = egg
    clearTimeout(timer)
    timer = setTimeout(() => (active.value = null), EGG_MS)
  }

  if (getCurrentScope()) onScopeDispose(() => clearTimeout(timer))

  return { active: readonly(active), celebrate }
}
