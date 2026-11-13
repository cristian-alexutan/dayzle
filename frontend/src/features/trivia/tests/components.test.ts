import { flushPromises } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import { mountWithPlugins } from '@/tests/utils'

import AnswerOption from '../components/AnswerOption.vue'
import QuestionCard from '../components/QuestionCard.vue'
import TriviaProgress from '../components/TriviaProgress.vue'
import TriviaResult from '../components/TriviaResult.vue'
import TriviaRules from '../components/TriviaRules.vue'
import type { ChoiceState } from '../types'
import { finishedGame, questions } from './fixtures'

describe('AnswerOption', () => {
  it('emits select when clicked', async () => {
    const wrapper = mountWithPlugins(AnswerOption, {
      props: { text: 'Cluj', letter: 'A', state: 'idle' },
    })
    await wrapper.trigger('click')
    expect(wrapper.emitted('select')).toHaveLength(1)
  })

  it.each<[ChoiceState, string, string | null]>([
    ['correct', 'answer-option--correct', 'Răspuns corect'],
    ['wrong', 'answer-option--wrong', 'Răspuns greșit'],
    ['dimmed', 'answer-option--dimmed', null],
  ])('shows the %s state', (state, cssClass, label) => {
    const wrapper = mountWithPlugins(AnswerOption, {
      props: { text: 'Cluj', letter: 'A', state, disabled: true },
    })
    expect(wrapper.classes()).toContain(cssClass)
    expect(wrapper.attributes('disabled')).toBeDefined()
    if (label) expect(wrapper.text()).toContain(label)
  })
})

describe('QuestionCard', () => {
  const question = questions[0]!

  it('shows the category, the question and its four choices', () => {
    const wrapper = mountWithPlugins(QuestionCard, {
      props: { question, choiceState: () => 'idle', selected: null },
    })
    expect(wrapper.find('[data-test="category"]').text()).toBe('Istorie')
    expect(wrapper.find('[data-test="question-text"]').text()).toBe('Question 1?')
    const options = wrapper.findAll('[data-test="answer-option"]')
    expect(options.map((option) => option.text())).toEqual([
      'AChoice 1.1',
      'BChoice 1.2',
      'CChoice 1.3',
      'DChoice 1.4',
    ])
  })

  it('emits the chosen choice id', async () => {
    const wrapper = mountWithPlugins(QuestionCard, {
      props: { question, choiceState: () => 'idle', selected: null },
    })
    await wrapper.findAll('[data-test="answer-option"]')[2]!.trigger('click')
    expect(wrapper.emitted('choose')).toEqual([[13]])
  })

  it('draws each choice with its state', () => {
    const wrapper = mountWithPlugins(QuestionCard, {
      props: {
        question,
        choiceState: (id: number) => (id === 11 ? 'correct' : id === 12 ? 'wrong' : 'dimmed'),
        selected: null,
        disabled: true,
      },
    })
    const classes = wrapper.findAll('[data-test="answer-option"]').map((option) => option.classes())
    expect(classes[0]).toContain('answer-option--correct')
    expect(classes[1]).toContain('answer-option--wrong')
    expect(classes[2]).toContain('answer-option--dimmed')
  })
})

describe('TriviaProgress', () => {
  it('shows the question number and a dot per outcome', () => {
    const wrapper = mountWithPlugins(TriviaProgress, {
      props: {
        current: 3,
        total: 5,
        outcomes: ['correct', 'wrong', 'pending', 'pending', 'pending'],
      },
    })
    expect(wrapper.find('[data-test="progress"]').text()).toBe('Întrebarea 3/5')
    const dots = wrapper.findAll('[data-test="progress-dot"]')
    expect(dots).toHaveLength(5)
    expect(dots[0]!.classes()).toContain('trivia-progress__dot--correct')
    expect(dots[1]!.classes()).toContain('trivia-progress__dot--wrong')
    expect(dots[2]!.classes()).toContain('trivia-progress__dot--current')
  })
})

describe('TriviaResult', () => {
  it('shows the score out of 5, the time and each question with its correct answer', () => {
    const wrapper = mountWithPlugins(TriviaResult, {
      props: { game: finishedGame([true, false, true, true, false], 83_000) },
    })
    expect(wrapper.text()).toContain('3/5')
    expect(wrapper.text()).toContain('1:23')
    expect(wrapper.find('[data-test="result-title"]').text()).toBe('Quiz terminat!')
    const rows = wrapper.findAll('[data-test="result-row"]')
    expect(rows).toHaveLength(5)
    expect(rows[1]!.classes()).toContain('trivia-result__row--wrong')
    expect(rows[1]!.text()).toContain('Choice 2.1')
  })

  it('celebrates a perfect quiz', () => {
    const wrapper = mountWithPlugins(TriviaResult, {
      props: { game: finishedGame([true, true, true, true, true]) },
    })
    expect(wrapper.text()).toContain('5/5')
    expect(wrapper.find('[data-test="result-title"]').text()).toContain('Perfect')
  })
})

describe('TriviaRules', () => {
  it('shows the rules and closes with its button', async () => {
    const rules = mountWithPlugins(TriviaRules, {
      props: { visible: true },
      attachTo: document.body,
    })
    await flushPromises()

    const dialog = document.body.querySelector('[data-test="rules"]')
    expect(dialog?.textContent).toContain('scorul e din 5')
    ;(document.body.querySelector('[data-test="rules-start"]') as HTMLElement).click()
    expect(rules.emitted('update:visible')![0]).toEqual([false])
    rules.unmount()
    document.body.innerHTML = ''
  })
})
