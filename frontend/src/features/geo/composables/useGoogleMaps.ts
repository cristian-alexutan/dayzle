// useGoogleMaps: creates a Google Maps object (a map or a panorama) in an element once mounted.
import { onBeforeUnmount, onMounted, ref, shallowRef, watch, type Ref } from 'vue'

import { browserKey, loadGoogleMaps, mapsAuthFailed } from './loadGoogleMaps'

/** `unavailable`: no browser key is configured. `error`: Google can't be loaded or refused it. */
export type MapsStatus = 'loading' | 'ready' | 'unavailable' | 'error'

let warnedAboutKey = false

/**
 * Load the Maps JavaScript API, then call `create` with the mounted `container`. `instance` is
 * what `create` returned, and null before that and after unmount.
 */
export function useGoogleMaps<T>(
  container: Ref<HTMLElement | null>,
  create: (element: HTMLElement) => Promise<T>,
) {
  const status = ref<MapsStatus>('loading')
  const instance = shallowRef<T | null>(null)
  let unmounted = false

  onMounted(async () => {
    const key = browserKey()
    if (!key) {
      status.value = 'unavailable'
      if (!warnedAboutKey) {
        warnedAboutKey = true
        console.warn('GeoGuesser: set VITE_GOOGLE_MAPS_BROWSER_KEY in frontend/.env for the maps.')
      }
      return
    }
    try {
      await loadGoogleMaps(key)
      if (unmounted || !container.value) return
      const created = await create(container.value)
      if (unmounted) return
      instance.value = created
      status.value = mapsAuthFailed.value ? 'error' : 'ready'
    } catch {
      if (!unmounted) status.value = 'error'
    }
  })

  watch(mapsAuthFailed, (failed) => {
    if (failed) status.value = 'error'
  })

  onBeforeUnmount(() => {
    unmounted = true
    instance.value = null
  })

  return { status, instance }
}
