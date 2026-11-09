<!-- RevealMap: guessed rounds on a map: the player's pin, the real spot and a line between. -->
<script setup lang="ts">
import { ref, watch } from 'vue'

import { pinOptions, themeColor, useRegionMap } from '../composables/useRegionMap'
import type { Bounds, RoundResult } from '../types'
import MapsStatusOverlay from './MapsStatusOverlay.vue'
import './map.css'

const props = defineProps<{
  bounds: Bounds
  results: RoundResult[]
  /** Write the round number on each real spot, for a map with several rounds. */
  numbered?: boolean
}>()

const container = ref<HTMLElement | null>(null)
const { status, instance } = useRegionMap(container, () => props.bounds)

/** Room around the pins, in pixels, when the map zooms to them. */
const FIT_PADDING = 48
/** Two pins a few metres apart shouldn't zoom in further than street level. */
const MAX_ZOOM = 16

let drawn: Array<{ setMap(map: null): void }> = []

function draw() {
  const kit = instance.value
  if (!kit) return
  drawn.forEach((shape) => shape.setMap(null))
  drawn = []
  if (props.results.length === 0) return

  const view = new kit.LatLngBounds()
  for (const result of props.results) {
    view.extend(result.guess)
    view.extend(result.location)
    drawn.push(
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
  kit.map.fitBounds(view, FIT_PADDING)
  const zoomed = kit.map.addListener('idle', () => {
    zoomed.remove()
    if ((kit.map.getZoom() ?? 0) > MAX_ZOOM) kit.map.setZoom(MAX_ZOOM)
  })
}

watch(instance, draw)
watch(() => props.results, draw, { deep: true })
</script>

<template>
  <div class="geo-frame" role="region">
    <div ref="container" class="geo-frame__view" data-test="reveal-map" />
    <MapsStatusOverlay :status="status" />
  </div>
</template>
