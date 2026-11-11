// useQuizProgress: where the player is in the quiz, rebuilt from the server's answers.
import { computed, ref, toValue, type MaybeRefOrGetter } from 'vue'

import type { Answer, ChoiceState, TriviaGame } from '../types'

export type QuestionOutcome = 'correct' | 'wrong' | 'pending'

/**
 * The current question is the first one without an answer, so a reload resumes the quiz where
 * the server left it. Right after an answer, that question stays on screen with its feedback
 * (`reviewing`) until the player moves on with `next()`.
 */
export function useQuizProgress(game: MaybeRefOrGetter<TriviaGame | undefined>) {
  const reviewing = ref<number | null>(null)

  const questions = computed(() => toValue(game)?.questions ?? [])
  const answersByQuestion = computed(
    () =>
      new Map<number, Answer>(
        (toValue(game)?.answers ?? []).map((answer) => [answer.question, answer]),
      ),
  )

  const completed = computed(() => toValue(game)?.status === 'completed')
  /** The quiz is over and the player has seen the last feedback. */
  const finished = computed(() => completed.value && reviewing.value === null)

  const currentIndex = computed(() => {
    if (reviewing.value !== null) {
      const index = questions.value.findIndex((question) => question.id === reviewing.value)
      if (index !== -1) return index
    }
    const next = questions.value.findIndex((question) => !answersByQuestion.value.has(question.id))
    return next === -1 ? Math.max(questions.value.length - 1, 0) : next
  })
  const currentQuestion = computed(() => questions.value[currentIndex.value])
  const currentAnswer = computed(() =>
    currentQuestion.value ? answersByQuestion.value.get(currentQuestion.value.id) : undefined,
  )
  const isLast = computed(() => currentIndex.value === questions.value.length - 1)

  const outcomes = computed<QuestionOutcome[]>(() =>
    questions.value.map((question) => {
      const answer = answersByQuestion.value.get(question.id)
      if (!answer) return 'pending'
      return answer.is_correct ? 'correct' : 'wrong'
    }),
  )

  /** How a choice of the current question is drawn. */
  function choiceState(choiceId: number): ChoiceState {
    const answer = currentAnswer.value
    if (!answer) return 'idle'
    if (choiceId === answer.correct_choice) return 'correct'
    if (choiceId === answer.choice) return 'wrong'
    return 'dimmed'
  }

  /** Keep the answered question on screen to show whether the answer was right. */
  function review(questionId: number) {
    reviewing.value = questionId
  }

  /** Move on to the next question, or to the result after the last one. */
  function next() {
    reviewing.value = null
  }

  return {
    currentIndex,
    currentQuestion,
    currentAnswer,
    isLast,
    outcomes,
    finished,
    reviewing,
    choiceState,
    review,
    next,
  }
}
