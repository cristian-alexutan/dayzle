// useStreetView: shows a Google Street View panorama in an element, without giving the place away.
import { toValue, watch, type MaybeRefOrGetter, type Ref } from 'vue'

import { useGoogleMaps } from './useGoogleMaps'

const START_POV = { heading: 0, pitch: 0 }

/**
 * Street View with everything that names the place turned off: no address box and no street
 * names. Players can still look around and walk along the road.
 */
export const PANORAMA_OPTIONS: google.maps.StreetViewPanoramaOptions = {
  addressControl: false,
  showRoadLabels: false,
  enableCloseButton: false,
  fullscreenControl: true,
  motionTracking: false,
  motionTrackingControl: false,
  linksControl: true,
  clickToGo: true,
  zoomControl: true,
  panControl: false,
}

/** Show panorama `id` the way every round starts: facing north, unzoomed. */
function showStart(panorama: google.maps.StreetViewPanorama, id: string) {
  panorama.setPano(id)
  panorama.setPov(START_POV)
  panorama.setZoom(0)
}

/**
 * Show the panorama `panoramaId` in `container`; each new one starts facing north, unzoomed.
 * `control`, when given, is placed on the panorama's top left as one of Google's own controls,
 * so it stays visible in Street View's fullscreen mode. `backToStart` returns to the round's
 * panorama after the player walked away from it.
 */
export function useStreetView(
  container: Ref<HTMLElement | null>,
  panoramaId: MaybeRefOrGetter<string>,
  control?: Ref<HTMLElement | null>,
) {
  const { status, instance } = useGoogleMaps(container, async (element) => {
    const [{ StreetViewPanorama }, { ControlPosition }] = await Promise.all([
      google.maps.importLibrary('streetView') as Promise<google.maps.StreetViewLibrary>,
      google.maps.importLibrary('core') as Promise<google.maps.CoreLibrary>,
    ])
    const panorama = new StreetViewPanorama(element, {
      ...PANORAMA_OPTIONS,
      pano: toValue(panoramaId),
      pov: START_POV,
      zoom: 0,
    })
    if (control?.value) panorama.controls[ControlPosition.LEFT_TOP]?.push(control.value)
    return panorama
  })

  watch(
    () => toValue(panoramaId),
    (id) => {
      if (instance.value) showStart(instance.value, id)
    },
  )

  function backToStart() {
    if (instance.value) showStart(instance.value, toValue(panoramaId))
  }

  return { status, backToStart }
}
