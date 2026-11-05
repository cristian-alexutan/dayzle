<!-- ResultCard: Summary of a finished game: its big result, game details and time. -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import { formatDuration } from '../utils/formatDuration'
import AppCard from './AppCard.vue'

defineProps<{ result: string; durationMs: number | null }>()

const { t } = useI18n()
</script>

<template>
  <AppCard class="result-card">
    <template #title>
      <span class="result-card__result">{{ result }}</span>
    </template>
    <template #content>
      <slot />
      <p v-if="durationMs !== null" class="result-card__time">
        <i class="pi pi-clock" aria-hidden="true" />
        {{ t('common.time') }}: {{ formatDuration(durationMs) }}
      </p>
    </template>
  </AppCard>
</template>

<style scoped>
.result-card {
  --p-card-background: transparent;
  --p-card-shadow: none;
  --p-card-body-padding: 0;
  text-align: center;
}

.result-card__result {
  color: var(--dz-accent-strong);
  font-size: 2.5rem;
  font-weight: 800;
}

.result-card__time {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0.75rem 0 0;
  color: var(--dz-text-muted);
}
</style>
