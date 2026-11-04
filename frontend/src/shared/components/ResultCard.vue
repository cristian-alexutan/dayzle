<!-- ResultCard: Card that summarises a finished game: its result, details and time. -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import { formatDuration } from '../utils/formatDuration'
import AppCard from './AppCard.vue'

defineProps<{ result: string; durationMs: number | null }>()

const { t } = useI18n()
</script>

<template>
  <AppCard>
    <template #title>{{ result }}</template>
    <template #content>
      <slot />
      <p v-if="durationMs !== null" class="result-card__time">
        {{ t('common.time') }}: {{ formatDuration(durationMs) }}
      </p>
    </template>
  </AppCard>
</template>

<style scoped>
.result-card__time {
  margin: 0.5rem 0 0;
}
</style>
