<!-- WordKeyboard: the Romanian on-screen keyboard. Each key shows its letter's best color. -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import AppButton from '@/shared/components/AppButton.vue'

import type { LetterColor } from '../types'

defineProps<{ colors: Record<string, LetterColor>; disabled?: boolean }>()
defineEmits<{ letter: [letter: string]; enter: []; backspace: [] }>()

const { t } = useI18n()

const ROWS = ['qwertyuiop', 'asdfghjkl', 'zxcvbnm', 'ăâîșț'].map((row) => Array.from(row))
const ACTIONS_ROW = 2
</script>

<template>
  <div class="word-keyboard" role="group" :aria-label="t('word.keyboard')">
    <div v-for="(row, rowIndex) in ROWS" :key="rowIndex" class="word-keyboard__row">
      <AppButton
        v-if="rowIndex === ACTIONS_ROW"
        class="word-keyboard__key word-keyboard__key--wide"
        :label="t('word.enter')"
        :disabled="disabled"
        severity="secondary"
        data-test="enter"
        @mousedown.prevent
        @click="$emit('enter')"
      />
      <AppButton
        v-for="letter in row"
        :key="letter"
        class="word-keyboard__key"
        :class="colors[letter] && `word-keyboard__key--${colors[letter]}`"
        :label="letter.toUpperCase()"
        :disabled="disabled"
        severity="secondary"
        :data-test="`key-${letter}`"
        @mousedown.prevent
        @click="$emit('letter', letter)"
      />
      <AppButton
        v-if="rowIndex === ACTIONS_ROW"
        class="word-keyboard__key word-keyboard__key--wide"
        icon="pi pi-delete-left"
        :aria-label="t('word.backspace')"
        :disabled="disabled"
        severity="secondary"
        data-test="backspace"
        @mousedown.prevent
        @click="$emit('backspace')"
      />
    </div>
  </div>
</template>

<style scoped>
.word-keyboard {
  display: grid;
  gap: 0.35rem;
  width: 100%;
}

.word-keyboard__row {
  display: flex;
  justify-content: center;
  gap: 0.25rem;
}

.word-keyboard__key {
  --key-background: var(--dz-key);
  --key-color: var(--dz-on-key);
  --p-button-secondary-background: var(--key-background);
  --p-button-secondary-hover-background: var(--key-background);
  --p-button-secondary-active-background: var(--key-background);
  --p-button-secondary-border-color: var(--key-background);
  --p-button-secondary-hover-border-color: var(--key-background);
  --p-button-secondary-active-border-color: var(--key-background);
  --p-button-secondary-color: var(--key-color);
  --p-button-secondary-hover-color: var(--key-color);
  --p-button-secondary-active-color: var(--key-color);
  flex: 1 1 0;
  min-width: 0;
  max-width: 2.75rem;
  height: 3.25rem;
  padding: 0;
  font-weight: 600;
}

.word-keyboard__key--wide {
  flex-grow: 1.6;
  max-width: 4.5rem;
  font-size: 0.8rem;
}

.word-keyboard__key--correct {
  --key-background: var(--dz-correct);
  --key-color: var(--dz-on-correct);
}

.word-keyboard__key--present {
  --key-background: var(--dz-present);
  --key-color: var(--dz-on-present);
}

.word-keyboard__key--absent {
  --key-background: var(--dz-absent);
  --key-color: var(--dz-on-absent);
}
</style>
