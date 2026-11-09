// usePinPlacement: where the player put their pin for the current round.
import { ref, toValue, watch, type MaybeRefOrGetter } from 'vue'

import type { Bounds, Point } from '../types'
import { isInside } from './useRegionMap'

/**
 * The pin on the guess map. A point outside the region is refused right away (the backend
 * would refuse it too), and the pin is cleared whenever the round changes.
 */
export function usePinPlacement(options: {
  bounds: MaybeRefOrGetter<Bounds | undefined>
  round: MaybeRefOrGetter<number | null | undefined>
}) {
  const pin = ref<Point | null>(null)
  /** True after a refused point, until the next accepted one. */
  const outside = ref(false)

  function place(point: Point) {
    const bounds = toValue(options.bounds)
    if (!bounds || !isInside(bounds, point)) {
      outside.value = true
      return
    }
    outside.value = false
    pin.value = { lat: point.lat, lng: point.lng }
  }

  function clear() {
    pin.value = null
    outside.value = false
  }

  watch(() => toValue(options.round), clear)

  return { pin, outside, place, clear }
}
