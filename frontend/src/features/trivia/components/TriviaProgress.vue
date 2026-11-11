<!-- TriviaProgress: "Question 2/5" and one dot per question, colored once it's answered. -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { QuestionOutcome } from '../composables/useQuizProgress'

defineProps<{ current: number; total: number; outcomes: QuestionOutcome[] }>()

const { t } = useI18n()
</script>

<template>
  <div class="trivia-progress">
    <span class="trivia-progress__label" data-test="progress">
      {{ t('trivia.progress', { current, total }) }}
    </span>
    <ol class="trivia-progress__dots" :aria-label="t('trivia.progressDots')">
      <li
        v-for="(outcome, index) in outcomes"
        :key="index"
        class="trivia-progress__dot"
        :class="[
          `trivia-progress__dot--${outcome}`,
          { 'trivia-progress__dot--current': index + 1 === current },
        ]"
        :aria-label="t(`trivia.outcome.${outcome}`, { number: index + 1 })"
        data-test="progress-dot"
      />
    </ol>
  </div>
</template>

<style scoped>
.trivia-progress {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 1rem;
}

.trivia-progress__label {
  color: var(--dz-text-muted);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.trivia-progress__dots {
  display: flex;
  gap: 0.4rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.trivia-progress__dot {
  width: 0.75rem;
  height: 0.75rem;
  border: 2px solid var(--dz-border-strong);
  border-radius: 50%;
}

.trivia-progress__dot--current {
  border-color: var(--dz-primary);
}

.trivia-progress__dot--correct {
  border-color: var(--dz-correct);
  background: var(--dz-correct);
}

.trivia-progress__dot--wrong {
  border-color: var(--dz-accent-strong);
  background: var(--dz-accent-strong);
}
</style>
