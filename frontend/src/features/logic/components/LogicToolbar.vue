<!-- LogicToolbar: the clock, mistakes and streak, and the buttons for X marks and the rules. -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import AppButton from '@/shared/components/AppButton.vue'
import { formatDuration } from '@/shared/utils/formatDuration'

defineProps<{
  elapsedMs: number
  mistakes: number
  streak: number
  canUndo: boolean
  hasMarks: boolean
  /** Hides the X buttons once the game is over. */
  playing: boolean
}>()

defineEmits<{ undo: []; clear: []; help: [] }>()

const { t } = useI18n()
</script>

<template>
  <div class="logic-toolbar">
    <div class="logic-toolbar__stats">
      <span class="logic-toolbar__item" :title="t('common.time')" data-test="time">
        <i class="pi pi-clock" aria-hidden="true" />
        {{ formatDuration(elapsedMs) }}
      </span>
      <span class="logic-toolbar__item" :title="t('logic.mistakes')" data-test="mistakes">
        <i class="pi pi-times-circle" aria-hidden="true" />
        <span>{{ t('logic.mistakes') }}:</span>
        {{ mistakes }}
      </span>
      <span class="logic-toolbar__item" :title="t('logic.streak')" data-test="streak">
        <i class="pi pi-bolt" aria-hidden="true" />
        <span>{{ t('logic.streak') }}:</span>
        ×{{ streak }}
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
          :disabled="!hasMarks"
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
