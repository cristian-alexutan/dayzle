<!--
  GeoMap: a Google map of the region. While guessing, a click puts the player's pin. With
  `results`, it shows the guessed rounds instead: the pin, the real spot and a line between.
  One map serves every round of a game, so Google is loaded once rather than for each reveal.
-->
<script setup lang="ts">
import { ref, watch } from 'vue'

import {
  onThemeChange,
  pinOptions,
  themeColor,
  useRegionMap,
  type RegionMap,
} from '../composables/useRegionMap'
import type { Bounds, Point, RoundResult } from '../types'
import MapsStatusOverlay from './MapsStatusOverlay.vue'
import './map.css'

const props = withDefaults(
  defineProps<{
    bounds: Bounds
    pin?: Point | null
    /** Guessed rounds to show; while there are any, clicks don't place a pin. */
    results?: RoundResult[]
    /** Write the round number on each real spot, for a map with several rounds. */
    numbered?: boolean
    disabled?: boolean
  }>(),
  { pin: null, results: () => [], numbered: false, disabled: false },
)
const emit = defineEmits<{ place: [point: Point] }>()

/** Room around the pins, in pixels, when the map zooms to the guessed rounds. */
const FIT_PADDING = 48
/** Two pins a few metres apart shouldn't zoom in further than street level. */
const MAX_ZOOM = 16

const container = ref<HTMLElement | null>(null)
const { status, instance } = useRegionMap(container, () => props.bounds)

let frame: google.maps.Rectangle | null = null
let marker: google.maps.Marker | null = null
let shapes: Array<{ setMap(map: null): void }> = []

function drawFrame(kit: RegionMap) {
  frame?.setMap(null)
  frame = new kit.Rectangle({
    map: kit.map,
    bounds: props.bounds,
    clickable: false,
    fillOpacity: 0,
    strokeColor: themeColor('--dz-primary-strong'),
    strokeWeight: 2,
  })
}

function drawPin() {
  const kit = instance.value
  if (!kit) return
  marker?.setMap(null)
  marker = props.pin ? new kit.Marker(pinOptions(kit, 'guess', props.pin)) : null
}

/** Draw the guessed rounds and zoom to them, or zoom back out to the region when there are none. */
function drawResults({ fit }: { fit: boolean }) {
  const kit = instance.value
  if (!kit) return
  shapes.forEach((shape) => shape.setMap(null))
  shapes = []
  if (props.results.length === 0) {
    if (fit) kit.map.fitBounds(props.bounds, 0)
    return
  }

  const view = new kit.LatLngBounds()
  for (const result of props.results) {
    view.extend(result.guess)
    view.extend(result.location)
    shapes.push(
      new kit.Polyline({
        map: kit.map,
        path: [result.guess, result.location],
        clickable: false,
        // A dashed line: Google draws dashes as repeated symbols on an invisible line.
        strokeOpacity: 0,
        icons: [
          {
            icon: {
              path: 'M 0,-1 0,1',
              strokeOpacity: 1,
              strokeColor: themeColor('--dz-text-muted'),
              scale: 2,
            },
            offset: '0',
            repeat: '10px',
          },
        ],
      }),
      new kit.Marker(pinOptions(kit, 'guess', result.guess)),
      new kit.Marker(
        pinOptions(kit, 'location', result.location, props.numbered ? result.round : undefined),
      ),
    )
  }
  if (!fit) return
  kit.map.fitBounds(view, FIT_PADDING)
  const zoomed = kit.map.addListener('idle', () => {
    zoomed.remove()
    if ((kit.map.getZoom() ?? 0) > MAX_ZOOM) kit.map.setZoom(MAX_ZOOM)
  })
}

watch(instance, (kit) => {
  if (!kit) return
  drawFrame(kit)
  kit.map.addListener('click', (event: google.maps.MapMouseEvent) => {
    if (props.disabled || props.results.length > 0 || !event.latLng) return
    emit('place', { lat: event.latLng.lat(), lng: event.latLng.lng() })
  })
  drawPin()
  // A map made for the end screen starts on its rounds; a guess map starts on the region.
  if (props.results.length > 0) drawResults({ fit: true })
})

watch(() => props.pin, drawPin)
watch(
  () => props.results,
  () => drawResults({ fit: true }),
  { deep: true },
)

onThemeChange(() => {
  const kit = instance.value
  if (!kit) return
  drawFrame(kit)
  drawPin()
  drawResults({ fit: false })
})
</script>

<template>
  <div class="geo-frame" role="region">
    <div ref="container" class="geo-frame__view" data-test="map" />
    <MapsStatusOverlay :status="status" />
  </div>
</template>
