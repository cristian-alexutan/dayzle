/// <reference types="google.maps" />
// loadGoogleMaps: loads Google's Maps JavaScript API once, for the panoramas and the maps.
import { ref } from 'vue'

declare global {
  interface Window {
    /** Called by Google when the key is refused (wrong key, API not enabled, wrong referrer). */
    gm_authFailure?: () => void
    __dayzleMapsReady?: () => void
  }
}

const SCRIPT_URL = 'https://maps.googleapis.com/maps/api/js'
const CALLBACK = '__dayzleMapsReady'

/** Set when Google refuses the key; the maps then show an error instead of a grey box. */
export const mapsAuthFailed = ref(false)

let scriptLoading: Promise<void> | null = null

/**
 * The browser key: `VITE_GOOGLE_MAPS_BROWSER_KEY`, a key of its own restricted to the site's
 * address and the Maps JavaScript API, never the backend's server key.
 */
export function browserKey(): string | undefined {
  return import.meta.env.VITE_GOOGLE_MAPS_BROWSER_KEY || undefined
}

function isLoaded() {
  const maps = (window as { google?: typeof google }).google?.maps
  return typeof maps?.importLibrary === 'function'
}

/** Load the API with the browser key, once. Later calls wait for the same load. */
export function loadGoogleMaps(key: string): Promise<void> {
  if (isLoaded()) return Promise.resolve()
  scriptLoading ??= new Promise<void>((resolve, reject) => {
    window.gm_authFailure = () => {
      mapsAuthFailed.value = true
    }
    window[CALLBACK] = () => {
      if (isLoaded()) resolve()
      else reject(new Error('Google Maps loaded without importLibrary.'))
    }
    const script = document.createElement('script')
    const query = new URLSearchParams({ key, v: 'weekly', loading: 'async', callback: CALLBACK })
    script.src = `${SCRIPT_URL}?${query}`
    script.async = true
    script.onerror = () => {
      // Let a later map try again, e.g. after the connection comes back.
      scriptLoading = null
      script.remove()
      reject(new Error('Google Maps could not be loaded.'))
    }
    document.head.append(script)
  })
  return scriptLoading
}
