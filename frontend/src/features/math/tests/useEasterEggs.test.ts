import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { effectScope } from 'vue'

import { EGG_MS, eggForStep, useEasterEggs } from '../composables/useEasterEggs'
import type { PlayedStep } from '../types'

const step = (left: number, op: PlayedStep['op'], right: number, result: number): PlayedStep => ({
  left,
  op,
  right,
  result,
})

describe('eggForStep', () => {
  it.each([
    [step(60, '+', 7, 67), 'hands'],
    [step(400, '+', 4, 404), 'glitch'],
    [step(310, '+', 4, 314), 'pi'],
    [step(7, '-', 6, 1), 'operators'],
    [step(6, '*', 7, 42), 'operators'],
    [step(100, '*', 2, 200), null],
    // A 6 with another number, or two 6s, is not a 6 and a 7.
    [step(6, '+', 6, 12), null],
    [step(76, '-', 6, 70), null],
  ] as const)('%o gives %s', (played, egg) => {
    expect(eggForStep(played)).toBe(egg)
  })
})

describe('useEasterEggs', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  function setup() {
    const scope = effectScope()
    const eggs = scope.run(() => useEasterEggs())!
    return { scope, eggs }
  }

  it('plays an egg for EGG_MS, then hides it', () => {
    const { scope, eggs } = setup()

    eggs.celebrate(step(60, '+', 7, 67))
    expect(eggs.active.value).toBe('hands')

    vi.advanceTimersByTime(EGG_MS - 1)
    expect(eggs.active.value).toBe('hands')
    vi.advanceTimersByTime(1)
    expect(eggs.active.value).toBeNull()
    scope.stop()
  })

  it('plays each egg only once per game', () => {
    const { scope, eggs } = setup()

    eggs.celebrate(step(60, '+', 7, 67))
    vi.advanceTimersByTime(EGG_MS)
    eggs.celebrate(step(60, '+', 7, 67))

    expect(eggs.active.value).toBeNull()
    scope.stop()
  })

  it('plays the next egg at once, with its own full time', () => {
    const { scope, eggs } = setup()

    eggs.celebrate(step(7, '-', 6, 1))
    vi.advanceTimersByTime(EGG_MS - 100)
    eggs.celebrate(step(310, '+', 4, 314))
    expect(eggs.active.value).toBe('pi')

    vi.advanceTimersByTime(EGG_MS - 1)
    expect(eggs.active.value).toBe('pi')
    scope.stop()
  })

  it('does nothing for an ordinary step', () => {
    const { scope, eggs } = setup()

    eggs.celebrate(step(100, '*', 2, 200))

    expect(eggs.active.value).toBeNull()
    scope.stop()
  })

  it('stops its timer when the page goes away', () => {
    const { scope, eggs } = setup()

    eggs.celebrate(step(60, '+', 7, 67))
    scope.stop()

    expect(vi.getTimerCount()).toBe(0)
  })
})
