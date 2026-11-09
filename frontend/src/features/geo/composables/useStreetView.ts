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

/** Show the panorama `panoramaId` in `container`; each new one starts facing north, unzoomed. */
export function useStreetView(
  container: Ref<HTMLElement | null>,
  panoramaId: MaybeRefOrGetter<string>,
) {
  const { status, instance } = useGoogleMaps(container, async (element) => {
    const { StreetViewPanorama } = (await google.maps.importLibrary(
      'streetView',
    )) as google.maps.StreetViewLibrary
    return new StreetViewPanorama(element, {
      ...PANORAMA_OPTIONS,
      pano: toValue(panoramaId),
      pov: START_POV,
      zoom: 0,
    })
  })

  watch(
    () => toValue(panoramaId),
    (id) => {
      const panorama = instance.value
      if (!panorama) return
      panorama.setPano(id)
      panorama.setPov(START_POV)
      panorama.setZoom(0)
    },
  )

  return { status }
}
