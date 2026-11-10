<!-- Timer: Visible timer for timed games. It only displays the time; the backend measures it. -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import { formatDuration } from '../utils/formatDuration'

defineProps<{ ms: number }>()

const { t } = useI18n()
</script>

<template>
  <span class="timer" :title="t('common.time')" role="timer">
    <i class="pi pi-clock" aria-hidden="true" />
    {{ formatDuration(ms) }}
  </span>
</template>

<style scoped>
.timer {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-variant-numeric: tabular-nums;
}
</style>
