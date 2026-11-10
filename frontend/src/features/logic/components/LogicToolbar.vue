<!-- LogicToolbar: the clock and mistakes, and the buttons to undo, clear and see the rules. -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import AppButton from '@/shared/components/AppButton.vue'
import Timer from '@/shared/components/Timer.vue'

defineProps<{
  elapsedMs: number
  mistakes: number
  canUndo: boolean
  canClear: boolean
  /** Hides the undo and clear buttons once the game is over. */
  playing: boolean
}>()

defineEmits<{ undo: []; clear: []; help: [] }>()

const { t } = useI18n()
</script>

<template>
  <div class="logic-toolbar">
    <div class="logic-toolbar__stats">
      <Timer :ms="elapsedMs" data-test="time" />
      <span class="logic-toolbar__item" :title="t('logic.mistakes')" data-test="mistakes">
        <i class="pi pi-times-circle" aria-hidden="true" />
        <span>{{ t('logic.mistakes') }}:</span>
        {{ mistakes }}
      </span>
    </div>
    <div class="logic-toolbar__actions">
      <template v-if="playing">
        <AppButton
          icon="pi pi-undo"
          :label="t('logic.toolbar.undo')"
          severity="secondary"
          text
          size="small"
          :disabled="!canUndo"
          data-test="undo"
          @click="$emit('undo')"
        />
        <AppButton
          icon="pi pi-eraser"
          :label="t('logic.toolbar.clear')"
          severity="secondary"
          text
          size="small"
          :disabled="!canClear"
          data-test="clear"
          @click="$emit('clear')"
        />
      </template>
      <AppButton
        icon="pi pi-question-circle"
        :label="t('logic.toolbar.help')"
        severity="secondary"
        text
        size="small"
        data-test="help"
        @click="$emit('help')"
      />
    </div>
  </div>
</template>

<style scoped>
.logic-toolbar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.logic-toolbar__stats {
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

.logic-toolbar__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.25rem;
}
</style>
