<!-- MapsStatusOverlay: covers a panorama or map while it loads, or when Google can't be used. -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import AppMessage from '@/shared/components/AppMessage.vue'
import AppSpinner from '@/shared/components/AppSpinner.vue'

import type { MapsStatus } from '../composables/useGoogleMaps'
import './map.css'

defineProps<{ status: MapsStatus }>()

const { t } = useI18n()
</script>

<template>
  <div v-if="status !== 'ready'" class="geo-frame__overlay">
    <AppSpinner v-if="status === 'loading'" :aria-label="t('geo.maps.loading')" />
    <AppMessage v-else severity="warn" data-test="maps-unavailable">
      {{ t('geo.maps.unavailable') }}
    </AppMessage>
  </div>
</template>
