<!-- StepHistory: the steps the server saved, numbered, with how many are left. -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { PlayedStep } from '../types'
import StepList from './StepList.vue'

defineProps<{ steps: PlayedStep[]; maxSteps: number }>()

const { t } = useI18n()
</script>

<template>
  <section class="step-history" data-test="history">
    <h2 class="step-history__heading">
      <span>{{ t('math.history.title') }}</span>
      <span class="step-history__count" data-test="history-count">
        {{ t('math.history.count', { count: steps.length, max: maxSteps }) }}
      </span>
    </h2>
    <StepList v-if="steps.length" :steps="steps" />
    <p v-else class="step-history__empty" data-test="history-empty">
      {{ t('math.history.empty') }}
    </p>
  </section>
</template>

<style scoped>
.step-history {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  width: 100%;
}

.step-history__heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem;
  margin: 0;
  font-size: 1rem;
  font-weight: 800;
}

.step-history__count {
  color: var(--dz-text-muted);
  font-size: 0.85rem;
  font-weight: 600;
}

.step-history__empty {
  margin: 0;
  color: var(--dz-text-muted);
  font-size: 0.9rem;
}
</style>
