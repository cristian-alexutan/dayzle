<!-- GeoMap: the guess map. A click puts the player's pin; the region's edge is drawn on it. -->
<script setup lang="ts">
import { ref, watch } from 'vue'

import { pinOptions, themeColor, useRegionMap } from '../composables/useRegionMap'
import type { Bounds, Point } from '../types'
import MapsStatusOverlay from './MapsStatusOverlay.vue'
import './map.css'

const props = defineProps<{ bounds: Bounds; pin: Point | null; disabled?: boolean }>()
const emit = defineEmits<{ place: [point: Point] }>()

const container = ref<HTMLElement | null>(null)
const { status, instance } = useRegionMap(container, () => props.bounds)
let marker: google.maps.Marker | null = null

function drawPin() {
  const kit = instance.value
  if (!kit) return
  if (!props.pin) {
    marker?.setMap(null)
    marker = null
  } else if (marker) {
    marker.setPosition(props.pin)
  } else {
    marker = new kit.Marker(pinOptions(kit, 'guess', props.pin))
  }
}

watch(instance, (kit) => {
  if (!kit) return
  new kit.Rectangle({
    map: kit.map,
    bounds: props.bounds,
    clickable: false,
    fillOpacity: 0,
    strokeColor: themeColor('--dz-primary-strong'),
    strokeWeight: 2,
  })
  kit.map.addListener('click', (event: google.maps.MapMouseEvent) => {
    if (props.disabled || !event.latLng) return
    emit('place', { lat: event.latLng.lat(), lng: event.latLng.lng() })
  })
  drawPin()
})

watch(() => props.pin, drawPin)
</script>

<template>
  <div class="geo-frame" role="region">
    <div ref="container" class="geo-frame__view" data-test="guess-map" />
    <MapsStatusOverlay :status="status" />
  </div>
</template>
