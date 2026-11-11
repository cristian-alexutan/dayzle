<!-- QuestionCard: the current question, its category and its four choices. -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import AppCard from '@/shared/components/AppCard.vue'

import type { ChoiceState, Question } from '../types'
import AnswerOption from './AnswerOption.vue'

const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

defineProps<{
  question: Question
  /** How each choice is drawn, by choice id. */
  choiceState: (choiceId: number) => ChoiceState
  selected: number | null
  disabled?: boolean
}>()
defineEmits<{ choose: [choiceId: number] }>()

const { t } = useI18n()
</script>

<template>
  <AppCard class="question-card" data-test="question-card">
    <template #content>
      <p class="question-card__category" data-test="category">
        {{ t(`trivia.categories.${question.category}`) }}
      </p>
      <h2 class="question-card__text" data-test="question-text">{{ question.text }}</h2>
      <div class="question-card__choices" role="group" :aria-label="question.text">
        <AnswerOption
          v-for="(choice, index) in question.choices"
          :key="choice.id"
          :text="choice.text"
          :letter="LETTERS[index] ?? String(index + 1)"
          :state="choiceState(choice.id)"
          :selected="selected === choice.id"
          :disabled="disabled"
          @select="$emit('choose', choice.id)"
        />
      </div>
    </template>
  </AppCard>
</template>

<style scoped>
.question-card {
  width: 100%;
}

.question-card__category {
  margin: 0 0 0.35rem;
  color: var(--dz-accent-strong);
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.question-card__text {
  margin: 0 0 1rem;
  font-size: 1.15rem;
  font-weight: 700;
  line-height: 1.4;
}

.question-card__choices {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
</style>
