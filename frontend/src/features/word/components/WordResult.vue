<!-- WordResult: the end-of-game dialog: 3/6 or X/6, the word and the time. -->
<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import AppDialog from '@/shared/components/AppDialog.vue'
import ResultCard from '@/shared/components/ResultCard.vue'

import type { WordGame } from '../types'

const props = defineProps<{ game: WordGame }>()
const visible = defineModel<boolean>('visible', { required: true })

const { t } = useI18n()

const result = computed(() => {
  const attempts = props.game.solved ? props.game.guesses.length : 'X'
  return `${attempts}/${props.game.max_attempts}`
})
const title = computed(() => t(props.game.solved ? 'word.result.won' : 'word.result.lost'))
</script>

<template>
  <AppDialog v-model:visible="visible" :header="title" :style="{ width: 'min(90vw, 24rem)' }">
    <ResultCard :result="result" :duration-ms="game.duration_ms">
      <p class="word-result__answer" data-test="answer">
        {{ t('word.result.answer') }}: <strong>{{ game.answer }}</strong>
      </p>
    </ResultCard>
  </AppDialog>
</template>

<style scoped>
.word-result__answer {
  margin: 0;
}

.word-result__answer strong {
  text-transform: uppercase;
}
</style>
