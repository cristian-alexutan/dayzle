<!-- LogicToolbar: the clock, the number of mistakes and the current streak. -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import { formatDuration } from '@/shared/utils/formatDuration'

defineProps<{ elapsedMs: number; mistakes: number; streak: number }>()

const { t } = useI18n()
</script>

<template>
  <div class="logic-toolbar">
    <span class="logic-toolbar__item" :title="t('common.time')" data-test="time">
      <i class="pi pi-clock" aria-hidden="true" />
      {{ formatDuration(elapsedMs) }}
    </span>
    <span class="logic-toolbar__item" :title="t('logic.mistakes')" data-test="mistakes">
      <i class="pi pi-times-circle" aria-hidden="true" />
      <span class="logic-toolbar__label">{{ t('logic.mistakes') }}:</span>
      {{ mistakes }}
    </span>
    <span class="logic-toolbar__item" :title="t('logic.streak')" data-test="streak">
      <i class="pi pi-bolt" aria-hidden="true" />
      <span class="logic-toolbar__label">{{ t('logic.streak') }}:</span>
      ×{{ streak }}
    </span>
  </div>
</template>

<style scoped>
.logic-toolbar {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 1.25rem;
  color: var(--dz-text-muted);
  font-variant-numeric: tabular-nums;
}

.logic-toolbar__item {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}
</style>
