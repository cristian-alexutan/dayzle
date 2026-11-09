import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { effectScope, nextTick, ref } from 'vue'

import { useTimer } from './useTimer'

function setVisibility(state: 'visible' | 'hidden') {
  Object.defineProperty(document, 'visibilityState', { configurable: true, value: state })
  document.dispatchEvent(new Event('visibilitychange'))
}

beforeEach(() => {
  vi.useFakeTimers()
  setVisibility('visible')
})

afterEach(() => {
  vi.useRealTimers()
})

describe('useTimer', () => {
  it('counts up from the server time while running', () => {
    const scope = effectScope()
    const running = ref(true)
    const elapsed = scope.run(() => useTimer(5000, running))!

    vi.advanceTimersByTime(3000)
    expect(elapsed.value).toBe(8000)

    running.value = false
    expect(elapsed.value).toBe(5000)
    scope.stop()
  })

  it('stops while the page is hidden', () => {
    const scope = effectScope()
    const elapsed = scope.run(() => useTimer(0, true))!

    vi.advanceTimersByTime(2000)
    setVisibility('hidden')
    vi.advanceTimersByTime(10 * 60_000)
    expect(elapsed.value).toBe(2000)

    setVisibility('visible')
    vi.advanceTimersByTime(1000)
    expect(elapsed.value).toBe(3000)
    scope.stop()
  })

  it('starts again from each new server time', async () => {
    const scope = effectScope()
    const serverMs = ref(0)
    const elapsed = scope.run(() => useTimer(serverMs, true))!

    vi.advanceTimersByTime(4000)
    serverMs.value = 10_000
    await nextTick()

    expect(elapsed.value).toBe(10_000)
    scope.stop()
  })
})
