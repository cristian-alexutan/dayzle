<!-- StreetViewPanorama: the round's Street View, or a message when it can't be shown. -->
<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { useStreetView } from '../composables/useStreetView'
import MapsStatusOverlay from './MapsStatusOverlay.vue'
import './map.css'

const props = defineProps<{ panoramaId: string }>()

const { t } = useI18n()

const container = ref<HTMLElement | null>(null)
const { status } = useStreetView(container, () => props.panoramaId)
</script>

<template>
  <div class="geo-frame" role="region" :aria-label="t('geo.panorama')">
    <div ref="container" class="geo-frame__view" data-test="panorama" />
    <MapsStatusOverlay :status="status" />
  </div>
</template>
