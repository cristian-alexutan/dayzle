import { describe, expect, it } from 'vitest'
import { ref } from 'vue'

import { useQuizProgress } from '../composables/useQuizProgress'
import type { TriviaGame } from '../types'
import { answerTo, finishedGame, makeGame } from './fixtures'

describe('useQuizProgress', () => {
  it('starts on the first question with every outcome pending', () => {
    const progress = useQuizProgress(makeGame())

    expect(progress.currentIndex.value).toBe(0)
    expect(progress.currentQuestion.value?.id).toBe(1)
    expect(progress.currentAnswer.value).toBeUndefined()
    expect(progress.outcomes.value).toEqual(Array(5).fill('pending'))
    expect(progress.finished.value).toBe(false)
  })

  it('resumes on the first unanswered question after a reload', () => {
    const progress = useQuizProgress(makeGame({ answers: [answerTo(1, true), answerTo(2, false)] }))

    expect(progress.currentQuestion.value?.id).toBe(3)
    expect(progress.outcomes.value).toEqual(['correct', 'wrong', 'pending', 'pending', 'pending'])
  })

  it('keeps an answered question on screen until the player moves on', () => {
    const game = ref<TriviaGame>(makeGame())
    const progress = useQuizProgress(game)

    game.value = makeGame({ answers: [answerTo(1, false)] })
    progress.review(1)
    expect(progress.currentQuestion.value?.id).toBe(1)
    expect(progress.currentAnswer.value?.is_correct).toBe(false)

    progress.next()
    expect(progress.currentQuestion.value?.id).toBe(2)
  })

  it('draws the correct choice, the wrong pick and dims the rest', () => {
    const game = ref<TriviaGame>(makeGame({ answers: [answerTo(1, false)] }))
    const progress = useQuizProgress(game)
    progress.review(1)

    expect(progress.choiceState(11)).toBe('correct')
    expect(progress.choiceState(12)).toBe('wrong')
    expect(progress.choiceState(13)).toBe('dimmed')
  })

  it('leaves choices idle before the answer', () => {
    const progress = useQuizProgress(makeGame())
    expect(progress.choiceState(11)).toBe('idle')
  })

  it('finishes only after the last feedback has been seen', () => {
    const game = ref<TriviaGame>(makeGame())
    const progress = useQuizProgress(game)

    game.value = finishedGame([true, true, true, true, false])
    progress.review(5)
    expect(progress.isLast.value).toBe(true)
    expect(progress.finished.value).toBe(false)

    progress.next()
    expect(progress.finished.value).toBe(true)
  })

  it('is finished straight away when a completed quiz loads', () => {
    expect(useQuizProgress(finishedGame([true, true, true, true, true])).finished.value).toBe(true)
  })

  it('has no question before the game loads', () => {
    const progress = useQuizProgress(undefined)
    expect(progress.currentQuestion.value).toBeUndefined()
    expect(progress.outcomes.value).toEqual([])
  })
})
