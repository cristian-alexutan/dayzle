<!-- StepHistory: the steps the server saved, numbered, with how many are left. -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import { OPERATOR_SYMBOLS, type PlayedStep } from '../types'

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
    <ol v-if="steps.length" class="step-history__steps">
      <li v-for="(step, index) in steps" :key="index" class="step-history__step" data-test="step">
        <span class="step-history__number" aria-hidden="true">{{ index + 1 }}</span>
        <span data-test="step-text">
          {{ step.left }} {{ OPERATOR_SYMBOLS[step.op] }} {{ step.right }} =
          <strong>{{ step.result }}</strong>
        </span>
      </li>
    </ol>
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

.step-history__steps {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.step-history__step {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--dz-border);
  border-radius: 0.75rem;
  background: var(--dz-surface);
  font-size: 1.05rem;
  font-variant-numeric: tabular-nums;
}

.step-history__number {
  display: grid;
  place-items: center;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  background: var(--dz-primary);
  color: var(--dz-on-primary);
  font-size: 0.8rem;
  font-weight: 800;
}

.step-history__empty {
  margin: 0;
  color: var(--dz-text-muted);
  font-size: 0.9rem;
}
</style>
