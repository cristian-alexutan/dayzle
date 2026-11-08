<!-- OperatorPicker: the four operations. The picked one stays highlighted. -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import AppButton from '@/shared/components/AppButton.vue'

import { OPERATOR_SYMBOLS, type Operator } from '../types'

defineProps<{ selected: Operator | null; disabled?: boolean }>()
defineEmits<{ choose: [op: Operator] }>()

const { t } = useI18n()

const OPERATORS: { op: Operator; name: string }[] = [
  { op: '+', name: 'add' },
  { op: '-', name: 'subtract' },
  { op: '*', name: 'multiply' },
  { op: '/', name: 'divide' },
]
</script>

<template>
  <div class="operator-picker" role="group" :aria-label="t('math.operators.label')">
    <AppButton
      v-for="{ op, name } in OPERATORS"
      :key="op"
      class="operator-picker__operator"
      :class="{ 'operator-picker__operator--selected': selected === op }"
      severity="secondary"
      :label="OPERATOR_SYMBOLS[op]"
      :aria-label="t(`math.operators.${name}`)"
      :aria-pressed="selected === op ? 'true' : 'false'"
      :disabled="disabled"
      :data-test="`operator-${name}`"
      @click="$emit('choose', op)"
    />
  </div>
</template>

<style scoped>
.operator-picker {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.625rem;
  width: 100%;
}

.operator-picker__operator {
  --operator-background: var(--dz-surface);
  --operator-color: var(--dz-text);
  --operator-border: var(--dz-border);
  --p-button-secondary-background: var(--operator-background);
  --p-button-secondary-hover-background: var(--operator-background);
  --p-button-secondary-active-background: var(--operator-background);
  --p-button-secondary-border-color: var(--operator-border);
  --p-button-secondary-hover-border-color: var(--operator-border);
  --p-button-secondary-active-border-color: var(--operator-border);
  --p-button-secondary-color: var(--operator-color);
  --p-button-secondary-hover-color: var(--operator-color);
  --p-button-secondary-active-color: var(--operator-color);
  height: 3.5rem;
  border-width: 2px;
  border-radius: 1rem;
  font-size: 1.75rem;
  font-weight: 800;
}

.operator-picker__operator--selected {
  --operator-background: var(--dz-primary-strong);
  --operator-color: var(--dz-on-primary-strong);
  --operator-border: var(--dz-primary-strong);
  box-shadow:
    0 0 0 3px var(--dz-page),
    0 0 0 6px var(--dz-primary-strong);
}
</style>
