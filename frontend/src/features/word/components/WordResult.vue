<!-- WordResult: the end-of-game dialog: the score out of 6 or X/6, the word in tiles, the time. -->
<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import AppDialog from '@/shared/components/AppDialog.vue'
import ResultCard from '@/shared/components/ResultCard.vue'

import type { WordGame } from '../types'
import WordTile from './WordTile.vue'

const props = defineProps<{ game: WordGame }>()
const visible = defineModel<boolean>('visible', { required: true })

const { t } = useI18n()

// The score out of the best possible one (6: solved on the first guess without hints), so
// hints show in the result: 4 guesses and 3 hints is 1/6. A failed game is X/6.
const result = computed(() => {
  const score = props.game.solved ? props.game.score : 'X'
  return `${score}/${props.game.max_attempts}`
})
const title = computed(() => t(props.game.solved ? 'word.result.won' : 'word.result.lost'))
const answerLetters = computed(() => Array.from(props.game.answer ?? ''))
const hintsUsed = computed(() => props.game.hints.length)
const summary = computed(() => {
  const guesses = t('word.result.guesses', props.game.guesses.length)
  return hintsUsed.value > 0 ? `${guesses} · ${t('word.result.hints', hintsUsed.value)}` : guesses
})
</script>

<template>
  <AppDialog v-model:visible="visible" :header="title" :style="{ width: 'min(90vw, 24rem)' }">
    <ResultCard :result="result" :duration-ms="game.duration_ms">
      <p class="word-result__summary" data-test="summary">{{ summary }}</p>
      <p class="word-result__label">{{ t('word.result.answer') }}</p>
      <div class="word-result__tiles" :aria-label="game.answer ?? undefined" data-test="answer">
        <WordTile
          v-for="(letter, index) in answerLetters"
          :key="index"
          :letter="letter"
          :color="game.solved ? 'correct' : 'accent'"
          aria-hidden="true"
          data-test="answer-tile"
        />
      </div>
    </ResultCard>
  </AppDialog>
</template>

<style scoped>
.word-result__label {
  margin: 0 0 0.5rem;
  color: var(--dz-text-muted);
}

.word-result__summary {
  margin: 0 0 0.75rem;
  color: var(--dz-text-muted);
}

.word-result__tiles {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: 1fr;
  gap: 0.35rem;
  width: min(100%, 15rem);
  margin: 0 auto;
}
</style>
