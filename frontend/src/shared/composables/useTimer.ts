// useTimer: the on-screen clock of timed games. It only displays time; the backend measures it.
import { computed, onScopeDispose, ref, toValue, watch, type MaybeRefOrGetter } from 'vue'

const TICK_MS = 1000

/**
 * Counts up from the server's time while `running` is true and the page is visible, like the
 * backend, which only counts active time. Every new value from the server starts the count
 * again, so the clock never drifts far from the real duration.
 */
export function useTimer(serverMs: MaybeRefOrGetter<number>, running: MaybeRefOrGetter<boolean>) {
  // Time counted on screen since the last value from the server.
  const localMs = ref(0)
  let lastTick = 0
  let timer: ReturnType<typeof setInterval> | undefined

  function counting() {
    return toValue(running) && document.visibilityState === 'visible'
  }

  function tick() {
    const now = Date.now()
    localMs.value += now - lastTick
    lastTick = now
  }

  function update() {
    clearInterval(timer)
    timer = undefined
    if (!counting()) return
    lastTick = Date.now()
    timer = setInterval(tick, TICK_MS)
  }

  watch(
    () => toValue(serverMs),
    () => {
      localMs.value = 0
      lastTick = Date.now()
    },
  )
  const stopWatching = watch(() => toValue(running), update, { immediate: true })
  document.addEventListener('visibilitychange', update)

  onScopeDispose(() => {
    stopWatching()
    document.removeEventListener('visibilitychange', update)
    clearInterval(timer)
  })

  return computed(() => toValue(serverMs) + (toValue(running) ? localMs.value : 0))
}
