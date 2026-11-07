import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { effectScope, nextTick, ref } from 'vue'

import { HEARTBEAT_INTERVAL_MS, useHeartbeat } from './useHeartbeat'

function setVisibility(state: DocumentVisibilityState) {
  vi.spyOn(document, 'visibilityState', 'get').mockReturnValue(state)
  document.dispatchEvent(new Event('visibilitychange'))
}

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
  vi.restoreAllMocks()
})

describe('useHeartbeat', () => {
  it('beats every interval while active and visible', () => {
    const send = vi.fn().mockResolvedValue(undefined)
    const scope = effectScope()
    scope.run(() => useHeartbeat(send, true))

    vi.advanceTimersByTime(HEARTBEAT_INTERVAL_MS * 2)

    expect(send).toHaveBeenCalledTimes(2)
    scope.stop()
  })

  it('stops while the page is hidden and resumes when it is visible', () => {
    const send = vi.fn().mockResolvedValue(undefined)
    const scope = effectScope()
    scope.run(() => useHeartbeat(send, true))

    setVisibility('hidden')
    vi.advanceTimersByTime(HEARTBEAT_INTERVAL_MS * 2)
    expect(send).not.toHaveBeenCalled()

    setVisibility('visible')
    vi.advanceTimersByTime(HEARTBEAT_INTERVAL_MS)
    expect(send).toHaveBeenCalledTimes(1)
    scope.stop()
  })

  it('stops when no longer active, for example when the game ends', async () => {
    const send = vi.fn().mockResolvedValue(undefined)
    const active = ref(true)
    const scope = effectScope()
    scope.run(() => useHeartbeat(send, active))

    active.value = false
    await nextTick()
    vi.advanceTimersByTime(HEARTBEAT_INTERVAL_MS * 2)

    expect(send).not.toHaveBeenCalled()
    scope.stop()
  })

  it('stops when its scope ends and ignores failed beats', async () => {
    const send = vi.fn().mockRejectedValue(new Error('offline'))
    const scope = effectScope()
    scope.run(() => useHeartbeat(send, true))

    await vi.advanceTimersByTimeAsync(HEARTBEAT_INTERVAL_MS)
    expect(send).toHaveBeenCalledTimes(1)

    scope.stop()
    vi.advanceTimersByTime(HEARTBEAT_INTERVAL_MS)
    expect(send).toHaveBeenCalledTimes(1)
  })
})
