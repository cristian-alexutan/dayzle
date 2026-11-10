<!-- StreetViewPanorama: the round's Street View, or a message when it can't be shown. -->
<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import AppButton from '@/shared/components/AppButton.vue'

import { useStreetView } from '../composables/useStreetView'
import MapsStatusOverlay from './MapsStatusOverlay.vue'
import './map.css'

const props = defineProps<{ panoramaId: string }>()

const { t } = useI18n()

const container = ref<HTMLElement | null>(null)
/** The "back to start" button: Google moves it into the panorama as one of its controls. */
const control = ref<HTMLElement | null>(null)
const { status, backToStart } = useStreetView(container, () => props.panoramaId, control)
</script>

<template>
  <div class="geo-frame" role="region" :aria-label="t('geo.panorama')">
    <div ref="container" class="geo-frame__view" data-test="panorama" />
    <!-- v-show, not v-if: Google keeps this element, so it must stay the same one. -->
    <div v-show="status === 'ready'" ref="control" class="street-view__control">
      <AppButton
        :label="t('geo.backToStart')"
        icon="pi pi-replay"
        severity="secondary"
        size="small"
        raised
        data-test="back-to-start"
        @click="backToStart"
      />
    </div>
    <MapsStatusOverlay :status="status" />
  </div>
</template>

<style scoped>
.street-view__control {
  margin: 0.625rem;
}
</style>
