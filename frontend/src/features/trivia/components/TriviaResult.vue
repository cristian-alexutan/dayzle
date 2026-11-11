<!-- TriviaResult: the end-of-quiz card: the score out of 5, each question's outcome, the time. -->
<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import ResultCard from '@/shared/components/ResultCard.vue'

import type { TriviaGame } from '../types'

const props = defineProps<{ game: TriviaGame }>()

const { t } = useI18n()

const score = computed(() => props.game.score ?? 0)
const result = computed(() => `${score.value}/${props.game.max_score}`)
const title = computed(() => {
  if (props.game.solved) return t('trivia.result.perfect')
  if (score.value === 0) return t('trivia.result.none')
  return t('trivia.result.done')
})
const rows = computed(() =>
  props.game.questions.map((question) => {
    const answer = props.game.answers.find((given) => given.question === question.id)
    const correct = question.choices.find((choice) => choice.id === answer?.correct_choice)
    return {
      id: question.id,
      text: question.text,
      correctText: correct?.text ?? '',
      isCorrect: answer?.is_correct === true,
    }
  }),
)
</script>

<template>
  <section class="trivia-result" data-test="result">
    <h2 class="trivia-result__title" data-test="result-title">{{ title }}</h2>
    <ResultCard :result="result" :duration-ms="game.duration_ms">
      <ol class="trivia-result__list">
        <li
          v-for="row in rows"
          :key="row.id"
          class="trivia-result__row"
          :class="row.isCorrect ? 'trivia-result__row--correct' : 'trivia-result__row--wrong'"
          :aria-label="t(row.isCorrect ? 'trivia.option.correct' : 'trivia.option.wrong')"
          data-test="result-row"
        >
          <i :class="row.isCorrect ? 'pi pi-check' : 'pi pi-times'" aria-hidden="true" />
          <span class="trivia-result__question">
            {{ row.text }}
            <span class="trivia-result__answer">{{ row.correctText }}</span>
          </span>
        </li>
      </ol>
      <p class="trivia-result__comeback">{{ t('trivia.result.comeback') }}</p>
    </ResultCard>
  </section>
</template>

<style scoped>
.trivia-result {
  width: 100%;
  text-align: center;
}

.trivia-result__title {
  margin: 0;
  font-size: 1.25rem;
}

.trivia-result__list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin: 0.5rem 0 0;
  padding: 0;
  list-style: none;
  text-align: left;
}

.trivia-result__row {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
}

.trivia-result__row .pi {
  margin-top: 0.2rem;
}

.trivia-result__row--correct .pi {
  color: var(--dz-primary-strong);
}

.trivia-result__row--wrong .pi {
  color: var(--dz-accent-strong);
}

.trivia-result__question {
  display: flex;
  flex-direction: column;
}

.trivia-result__answer {
  color: var(--dz-text-muted);
  font-size: 0.9rem;
}

.trivia-result__comeback {
  margin: 1rem 0 0;
  color: var(--dz-text-muted);
}
</style>
