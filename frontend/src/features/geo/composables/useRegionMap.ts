// useRegionMap: a Google map of the region being played, and helpers to draw the rounds on it.
import { toValue, type MaybeRefOrGetter, type Ref } from 'vue'

import type { Bounds, Point } from '../types'
import { useGoogleMaps } from './useGoogleMaps'

/** How far past the region the player may pan, as a share of its size. */
const PAN_MARGIN = 0.25

/**
 * A plain map: no Street View pegman (it would show the place), no map type switch, and points of
 * interest that can't be clicked, so a click always places the pin.
 */
export const MAP_OPTIONS: google.maps.MapOptions = {
  disableDefaultUI: true,
  zoomControl: true,
  fullscreenControl: true,
  streetViewControl: false,
  clickableIcons: false,
  gestureHandling: 'greedy',
}

/** The map and the Google classes the components draw with. */
export interface RegionMap {
  map: google.maps.Map
  Marker: typeof google.maps.Marker
  Polyline: typeof google.maps.Polyline
  Rectangle: typeof google.maps.Rectangle
  LatLngBounds: typeof google.maps.LatLngBounds
  circle: google.maps.SymbolPath
}

/** Whether a point lies inside the region, edges included: the backend refuses any other guess. */
export function isInside({ south, west, north, east }: Bounds, { lat, lng }: Point) {
  return south <= lat && lat <= north && west <= lng && lng <= east
}

/** Google draws its markers itself, so they take the theme's colors as values, not variables. */
export function themeColor(variable: string) {
  return getComputedStyle(document.documentElement).getPropertyValue(variable).trim()
}

const PIN_COLORS = {
  guess: { fill: '--dz-accent', text: '--dz-on-accent' },
  location: { fill: '--dz-primary-strong', text: '--dz-on-primary-strong' },
}

/** A round pin: the player's guess (pink) or the real location (green). */
export function pinOptions(
  kit: RegionMap,
  kind: 'guess' | 'location',
  position: Point,
  label?: number,
): google.maps.MarkerOptions {
  const colors = PIN_COLORS[kind]
  return {
    map: kit.map,
    position,
    clickable: false,
    icon: {
      path: kit.circle,
      scale: 10,
      fillColor: themeColor(colors.fill),
      fillOpacity: 1,
      strokeColor: themeColor('--dz-surface'),
      strokeWeight: 3,
    },
    label:
      label === undefined
        ? undefined
        : {
            text: String(label),
            color: themeColor(colors.text),
            fontSize: '11px',
            fontWeight: '800',
          },
  }
}

function padded({ south, west, north, east }: Bounds): Bounds {
  const lat = (north - south) * PAN_MARGIN
  const lng = (east - west) * PAN_MARGIN
  return { south: south - lat, west: west - lng, north: north + lat, east: east + lng }
}

/**
 * Create a map showing the whole region in `container`. Players can't pan far away from it.
 * `status` is `unavailable` without a browser key and `error` when Google fails.
 */
export function useRegionMap(container: Ref<HTMLElement | null>, bounds: MaybeRefOrGetter<Bounds>) {
  return useGoogleMaps<RegionMap>(container, async (element) => {
    const [maps, markers, core] = await Promise.all([
      google.maps.importLibrary('maps') as Promise<google.maps.MapsLibrary>,
      google.maps.importLibrary('marker') as Promise<google.maps.MarkerLibrary>,
      google.maps.importLibrary('core') as Promise<google.maps.CoreLibrary>,
    ])
    const region = toValue(bounds)
    const map = new maps.Map(element, {
      ...MAP_OPTIONS,
      restriction: { latLngBounds: padded(region), strictBounds: false },
    })
    map.fitBounds(region, 0)
    return {
      map,
      Marker: markers.Marker,
      Polyline: maps.Polyline,
      Rectangle: maps.Rectangle,
      LatLngBounds: core.LatLngBounds,
      circle: core.SymbolPath.CIRCLE,
    }
  })
}
