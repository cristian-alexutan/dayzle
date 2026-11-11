<!-- AnswerOption: one choice of a question; after the answer it shows right, wrong or neither. -->
<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { ChoiceState } from '../types'

const props = defineProps<{
  text: string
  letter: string
  state: ChoiceState
  selected?: boolean
  disabled?: boolean
}>()
defineEmits<{ select: [] }>()

const { t } = useI18n()

const stateLabel = computed(() => {
  if (props.state === 'correct') return t('trivia.option.correct')
  if (props.state === 'wrong') return t('trivia.option.wrong')
  return null
})
const icon = computed(() => {
  if (props.state === 'correct') return 'pi pi-check'
  if (props.state === 'wrong') return 'pi pi-times'
  return null
})
</script>

<template>
  <button
    type="button"
    class="answer-option"
    :class="[`answer-option--${state}`, { 'answer-option--selected': selected }]"
    :disabled="disabled"
    :aria-pressed="selected ? 'true' : 'false'"
    data-test="answer-option"
    @click="$emit('select')"
  >
    <span class="answer-option__letter" aria-hidden="true">{{ letter }}</span>
    <span class="answer-option__text">{{ text }}</span>
    <i v-if="icon" :class="icon" class="answer-option__icon" aria-hidden="true" />
    <span v-if="stateLabel" class="answer-option__sr">{{ stateLabel }}</span>
  </button>
</template>

<style scoped>
.answer-option {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  min-height: 3rem;
  padding: 0.6rem 0.85rem;
  border: 2px solid var(--dz-border);
  border-radius: 0.75rem;
  background: var(--dz-surface);
  color: var(--dz-text);
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    border-color 0.15s,
    background-color 0.15s,
    opacity 0.15s;
}

.answer-option:hover:not(:disabled) {
  border-color: var(--dz-primary);
}

.answer-option:focus-visible {
  outline: 2px solid var(--dz-primary-strong);
  outline-offset: 2px;
}

.answer-option:disabled {
  cursor: default;
}

.answer-option--selected {
  border-color: var(--dz-primary);
}

.answer-option__letter {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 50%;
  background: var(--dz-key);
  color: var(--dz-on-key);
  font-weight: 700;
}

.answer-option__text {
  flex: 1;
}

.answer-option--correct {
  border-color: var(--dz-correct);
  background: var(--dz-correct);
  color: var(--dz-on-correct);
}

.answer-option--wrong {
  border-color: var(--dz-accent-strong);
  color: var(--dz-accent-strong);
}

.answer-option--dimmed {
  opacity: 0.55;
}

/* Read by screen readers only: the color and icon say the same to sighted players. */
.answer-option__sr {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}
</style>
