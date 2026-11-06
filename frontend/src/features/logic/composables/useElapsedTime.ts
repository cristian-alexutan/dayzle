// useElapsedTime: the on-screen clock. It only displays time; the backend measures it.
import { computed, onScopeDispose, ref, toValue, watch, type MaybeRefOrGetter } from 'vue'

const TICK_MS = 1000

/**
 * Counts up from the server's `elapsed_ms` while `running` is true. Every new value from the
 * server resets the count, so the clock never drifts far from the real duration.
 */
export function useElapsedTime(
  serverMs: MaybeRefOrGetter<number>,
  running: MaybeRefOrGetter<boolean>,
) {
  const syncedAt = ref(Date.now())
  const now = ref(Date.now())
  let timer: ReturnType<typeof setInterval> | undefined

  watch(
    () => toValue(serverMs),
    () => {
      syncedAt.value = Date.now()
      now.value = syncedAt.value
    },
  )

  watch(
    () => toValue(running),
    (isRunning) => {
      clearInterval(timer)
      timer = undefined
      if (!isRunning) return
      syncedAt.value = Date.now()
      now.value = syncedAt.value
      timer = setInterval(() => (now.value = Date.now()), TICK_MS)
    },
    { immediate: true },
  )

  onScopeDispose(() => clearInterval(timer))

  return computed(
    () => toValue(serverMs) + (toValue(running) ? Math.max(0, now.value - syncedAt.value) : 0),
  )
}
