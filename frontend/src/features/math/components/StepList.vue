<!-- StepList: steps as a numbered list, "100 × 2 = 200", as players write them. -->
<script setup lang="ts">
import { OPERATOR_SYMBOLS, type PlayedStep } from '../types'

defineProps<{ steps: PlayedStep[] }>()
</script>

<template>
  <ol class="step-list">
    <li v-for="(step, index) in steps" :key="index" class="step-list__step" data-test="step">
      <span class="step-list__number" aria-hidden="true">{{ index + 1 }}</span>
      <span data-test="step-text">
        {{ step.left }} {{ OPERATOR_SYMBOLS[step.op] }} {{ step.right }} =
        <strong>{{ step.result }}</strong>
      </span>
    </li>
  </ol>
</template>

<style scoped>
.step-list {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.step-list__step {
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

.step-list__number {
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
</style>
