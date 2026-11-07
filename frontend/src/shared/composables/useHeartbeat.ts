import { onScopeDispose, toValue, watch, type MaybeRefOrGetter } from 'vue'

/** How often the backend expects a heartbeat; see ACTIVITY_GAP_CAP in results/services.py. */
export const HEARTBEAT_INTERVAL_MS = 15_000

/**
 * Tell the backend the player is still here, so thinking time counts as active: calls `send`
 * every 15 s while `active` is true and the page is visible. A failed beat is ignored, since the
 * next one or the player's next move makes up for it.
 */
export function useHeartbeat(send: () => Promise<unknown>, active: MaybeRefOrGetter<boolean>) {
  let timer: ReturnType<typeof setInterval> | undefined

  function update() {
    clearInterval(timer)
    timer = undefined
    if (toValue(active) && document.visibilityState === 'visible') {
      timer = setInterval(() => {
        send().catch(() => {})
      }, HEARTBEAT_INTERVAL_MS)
    }
  }

  const stopWatching = watch(() => toValue(active), update, { immediate: true })
  document.addEventListener('visibilitychange', update)

  onScopeDispose(() => {
    stopWatching()
    document.removeEventListener('visibilitychange', update)
    clearInterval(timer)
  })
}
