<!-- TriviaGameView: the daily 5-question quiz inside the shared game frame. -->
<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import AppButton from '@/shared/components/AppButton.vue'
import AppMessage from '@/shared/components/AppMessage.vue'
import AppSpinner from '@/shared/components/AppSpinner.vue'
import ErrorState from '@/shared/components/ErrorState.vue'
import GameShell from '@/shared/components/GameShell.vue'

import {
  errorCode,
  useAnswerMutation,
  useTriviaGameQuery,
  useTriviaHeartbeat,
} from '../api/queries'
import QuestionCard from '../components/QuestionCard.vue'
import TriviaProgress from '../components/TriviaProgress.vue'
import TriviaResult from '../components/TriviaResult.vue'
import { useQuizProgress } from '../composables/useQuizProgress'

const DAY = 'today'
/**
 * Errors after which the server knows better than this page: reload the quiz from it. `invalid`
 * and `no_puzzle` come back when the day changed while the quiz was open (an answer sent just
 * after midnight): the reload then shows the new day's quiz, or that there is none.
 */
const RESYNC_CODES = new Set([
  'already_played',
  'already_answered',
  'out_of_order',
  'invalid',
  'no_puzzle',
])

const { t } = useI18n()

const query = useTriviaGameQuery(DAY)
const answer = useAnswerMutation(DAY)

const game = computed(() => query.data.value)
const inProgress = computed(() => game.value?.status === 'in_progress')
const noPuzzle = computed(() => errorCode(query.error.value) === 'no_puzzle')

const progress = useQuizProgress(game)
const { currentQuestion, currentAnswer, finished } = progress

useTriviaHeartbeat(DAY, inProgress)

/** The choice being sent, highlighted until the server answers. */
const selected = ref<number | null>(null)
const answerError = ref<string | null>(null)

const correctText = computed(() => {
  const given = currentAnswer.value
  return currentQuestion.value?.choices.find((choice) => choice.id === given?.correct_choice)?.text
})

function choose(choiceId: number) {
  const question = currentQuestion.value
  if (!question || currentAnswer.value || answer.isPending.value) return
  selected.value = choiceId
  answerError.value = null
  answer.mutate(
    { question: question.id, choice: choiceId },
    {
      onSuccess: () => progress.review(question.id),
      onError: (error) => {
        const code = errorCode(error)
        if (code !== null && RESYNC_CODES.has(code)) query.refetch()
        else answerError.value = t('trivia.errors.answer')
      },
      onSettled: () => (selected.value = null),
    },
  )
}
</script>

<template>
  <GameShell :title="t('trivia.title')" data-test="trivia-game">
    <AppSpinner
      v-if="query.isPending.value"
      :aria-label="t('trivia.loading')"
      data-test="loading"
    />
    <AppMessage v-else-if="noPuzzle" severity="info" data-test="no-puzzle">
      {{ t('trivia.noPuzzle') }}
    </AppMessage>
    <ErrorState
      v-else-if="query.isError.value"
      :message="t('trivia.errors.generic')"
      retryable
      data-test="load-error"
      @retry="query.refetch()"
    />
    <template v-else-if="game">
      <TriviaResult v-if="finished" :game="game" />
      <template v-else-if="currentQuestion">
        <TriviaProgress
          :current="progress.currentIndex.value + 1"
          :total="game.questions.length"
          :outcomes="progress.outcomes.value"
        />
        <QuestionCard
          :question="currentQuestion"
          :choice-state="progress.choiceState"
          :selected="selected"
          :disabled="!!currentAnswer || answer.isPending.value"
          @choose="choose"
        />
        <div class="trivia-game__feedback" aria-live="polite">
          <AppMessage v-if="answerError" severity="error" size="small" data-test="answer-error">
            {{ answerError }}
          </AppMessage>
          <p
            v-else-if="currentAnswer"
            class="trivia-game__verdict"
            :class="
              currentAnswer.is_correct
                ? 'trivia-game__verdict--right'
                : 'trivia-game__verdict--wrong'
            "
            data-test="feedback"
          >
            <template v-if="currentAnswer.is_correct">{{ t('trivia.feedback.right') }}</template>
            <template v-else>{{ t('trivia.feedback.wrong', { answer: correctText }) }}</template>
          </p>
        </div>
        <AppButton
          v-if="currentAnswer"
          :label="progress.isLast.value ? t('trivia.seeResult') : t('trivia.next')"
          :icon="progress.isLast.value ? 'pi pi-trophy' : 'pi pi-arrow-right'"
          icon-pos="right"
          rounded
          data-test="next"
          @click="progress.next()"
        />
      </template>
    </template>
  </GameShell>
</template>

<style scoped>
/* Space kept for the feedback, so the button doesn't jump when it appears. */
.trivia-game__feedback {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 1.75rem;
}

.trivia-game__verdict {
  margin: 0;
  font-weight: 700;
  text-align: center;
}

.trivia-game__verdict--right {
  color: var(--dz-primary-strong);
}

.trivia-game__verdict--wrong {
  color: var(--dz-accent-strong);
}
</style>
