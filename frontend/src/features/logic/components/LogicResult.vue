<!-- LogicResult: the end-of-game dialog: the score out of 1000, the mistakes and the time. -->
<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import AppDialog from '@/shared/components/AppDialog.vue'
import ResultCard from '@/shared/components/ResultCard.vue'

import type { LogicGame } from '../types'

const props = defineProps<{ game: LogicGame }>()
const visible = defineModel<boolean>('visible', { required: true })

const { t } = useI18n()

const result = computed(() => `${props.game.score ?? 0}/1000`)
</script>

<template>
  <AppDialog
    v-model:visible="visible"
    :header="t('logic.result.title')"
    :style="{ width: 'min(90vw, 24rem)' }"
  >
    <ResultCard :result="result" :duration-ms="game.duration_ms">
      <p class="logic-result__mistakes" data-test="result-mistakes">
        {{ t('logic.result.mistakes', { count: game.mistakes }, game.mistakes) }}
      </p>
    </ResultCard>
  </AppDialog>
</template>

<style scoped>
.logic-result__mistakes {
  margin: 0;
  color: var(--dz-text-muted);
}
</style>
