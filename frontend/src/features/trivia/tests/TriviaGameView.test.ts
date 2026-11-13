import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { mountWithPlugins } from '@/tests/utils'

import TriviaGameView from '../views/TriviaGameView.vue'
import { answerTo, errorResponse, finishedGame, jsonResponse, makeGame } from './fixtures'

const fetchMock = vi.fn()

async function mountView(firstResponse: Response) {
  fetchMock.mockResolvedValueOnce(firstResponse)
  const wrapper = mountWithPlugins(TriviaGameView)
  await flushPromises()
  return wrapper
}

function options(wrapper: Awaited<ReturnType<typeof mountView>>) {
  return wrapper.findAll('[data-test="answer-option"]')
}

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock)
  // Most tests are about playing, so the first-time rules dialog stays closed.
  localStorage.setItem('dayzle.trivia.rulesSeen', 'yes')
})

afterEach(() => {
  localStorage.clear()
  fetchMock.mockReset()
  vi.unstubAllGlobals()
  document.body.innerHTML = ''
})

const rulesDialog = () => document.body.querySelector('[data-test="rules"]')
const clickRulesStart = () =>
  (document.body.querySelector('[data-test="rules-start"]') as HTMLElement).click()

describe('TriviaGameView', () => {
  it('shows a spinner while loading', () => {
    fetchMock.mockReturnValueOnce(new Promise(() => {}))
    const wrapper = mountWithPlugins(TriviaGameView)
    expect(wrapper.find('[data-test="loading"]').exists()).toBe(true)
  })

  it('shows the first question with the progress 1/5', async () => {
    const wrapper = await mountView(jsonResponse(200, makeGame()))

    expect(fetchMock.mock.calls[0]![0]).toBe('/api/v1/games/trivia/today/')
    expect(wrapper.find('[data-test="progress"]').text()).toBe('Întrebarea 1/5')
    expect(wrapper.find('[data-test="question-text"]').text()).toBe('Question 1?')
    expect(wrapper.find('[data-test="next"]').exists()).toBe(false)
  })

  it('sends the answer, shows right feedback, then moves on', async () => {
    const wrapper = await mountView(jsonResponse(200, makeGame()))
    fetchMock.mockResolvedValueOnce(jsonResponse(200, makeGame({ answers: [answerTo(1, true)] })))

    await options(wrapper)[0]!.trigger('click')
    await flushPromises()

    const [url, init] = fetchMock.mock.calls[1]!
    expect(url).toBe('/api/v1/games/trivia/today/answer/')
    expect(init.body).toBe(JSON.stringify({ question: 1, choice: 11 }))
    expect(wrapper.find('[data-test="feedback"]').text()).toBe('Corect!')
    expect(options(wrapper)[0]!.classes()).toContain('answer-option--correct')
    expect(options(wrapper)[0]!.attributes('disabled')).toBeDefined()

    await wrapper.find('[data-test="next"]').trigger('click')
    expect(wrapper.find('[data-test="question-text"]').text()).toBe('Question 2?')
    expect(wrapper.find('[data-test="progress"]').text()).toBe('Întrebarea 2/5')
    expect(wrapper.find('[data-test="feedback"]').exists()).toBe(false)
  })

  it('shows the correct answer after a wrong one', async () => {
    const wrapper = await mountView(jsonResponse(200, makeGame()))
    fetchMock.mockResolvedValueOnce(jsonResponse(200, makeGame({ answers: [answerTo(1, false)] })))

    await options(wrapper)[1]!.trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-test="feedback"]').text()).toBe(
      'Greșit. Răspunsul corect: Choice 1.1',
    )
    expect(options(wrapper)[1]!.classes()).toContain('answer-option--wrong')
    expect(options(wrapper)[0]!.classes()).toContain('answer-option--correct')
  })

  it('resumes mid-quiz from the server state', async () => {
    const wrapper = await mountView(
      jsonResponse(200, makeGame({ answers: [answerTo(1, true), answerTo(2, false)] })),
    )

    expect(wrapper.find('[data-test="question-text"]').text()).toBe('Question 3?')
    expect(wrapper.find('[data-test="progress"]').text()).toBe('Întrebarea 3/5')
  })

  it('shows the result card after the last feedback', async () => {
    const before = makeGame({ answers: [1, 2, 3, 4].map((id) => answerTo(id, true)) })
    const wrapper = await mountView(jsonResponse(200, before))
    fetchMock.mockResolvedValueOnce(
      jsonResponse(200, finishedGame([true, true, true, true, false])),
    )

    await options(wrapper)[3]!.trigger('click')
    await flushPromises()
    const next = wrapper.find('[data-test="next"]')
    expect(next.text()).toBe('Vezi rezultatul')
    expect(wrapper.find('[data-test="result"]').exists()).toBe(false)

    await next.trigger('click')
    expect(wrapper.find('[data-test="result"]').text()).toContain('4/5')
  })

  it('shows the result straight away for a quiz already played', async () => {
    const wrapper = await mountView(jsonResponse(200, finishedGame([true, true, true, true, true])))

    expect(wrapper.find('[data-test="result"]').text()).toContain('5/5')
    expect(wrapper.find('[data-test="question-card"]').exists()).toBe(false)
  })

  it('reloads the quiz when the server says it is out of sync', async () => {
    const wrapper = await mountView(jsonResponse(200, makeGame()))
    fetchMock
      .mockResolvedValueOnce(errorResponse(409, 'already_answered'))
      .mockResolvedValueOnce(jsonResponse(200, makeGame({ answers: [answerTo(1, true)] })))

    await options(wrapper)[0]!.trigger('click')
    await flushPromises()

    expect(fetchMock.mock.calls[2]![0]).toBe('/api/v1/games/trivia/today/')
    expect(wrapper.find('[data-test="question-text"]').text()).toBe('Question 2?')
  })

  it('shows an error when the answer could not be sent, and allows a retry', async () => {
    const wrapper = await mountView(jsonResponse(200, makeGame()))
    fetchMock.mockResolvedValueOnce(errorResponse(500, 'server_error'))

    await options(wrapper)[0]!.trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-test="answer-error"]').exists()).toBe(true)
    expect(options(wrapper)[0]!.attributes('disabled')).toBeUndefined()
  })

  it('shows the new day after an answer sent past midnight', async () => {
    const wrapper = await mountView(jsonResponse(200, makeGame()))
    const nextDay = makeGame({
      date: '2026-11-12',
      questions: makeGame().questions.map((question) => ({
        ...question,
        text: `Tomorrow ${question.text}`,
      })),
    })
    fetchMock
      .mockResolvedValueOnce(errorResponse(400, 'invalid'))
      .mockResolvedValueOnce(jsonResponse(200, nextDay))

    await options(wrapper)[0]!.trigger('click')
    await flushPromises()

    expect(fetchMock.mock.calls[2]![0]).toBe('/api/v1/games/trivia/today/')
    expect(wrapper.find('[data-test="question-text"]').text()).toBe('Tomorrow Question 1?')
    expect(wrapper.find('[data-test="answer-error"]').exists()).toBe(false)
  })

  it('says there is no quiz when the new day has none', async () => {
    const wrapper = await mountView(jsonResponse(200, makeGame()))
    fetchMock
      .mockResolvedValueOnce(errorResponse(404, 'no_puzzle'))
      .mockResolvedValueOnce(errorResponse(404, 'no_puzzle'))

    await options(wrapper)[0]!.trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-test="no-puzzle"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="question-card"]').exists()).toBe(false)
  })

  it('says when there is no quiz today', async () => {
    const wrapper = await mountView(errorResponse(404, 'no_puzzle'))
    expect(wrapper.find('[data-test="no-puzzle"]').text()).toContain('Nu există quiz pentru azi')
  })

  it('shows an error with a retry when the quiz fails to load', async () => {
    const wrapper = await mountView(errorResponse(500, 'server_error'))
    expect(wrapper.find('[data-test="load-error"]').exists()).toBe(true)

    fetchMock.mockResolvedValueOnce(jsonResponse(200, makeGame()))
    await wrapper.find('[data-test="load-error"] button').trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-test="question-card"]').exists()).toBe(true)
  })

  it('opens the rules the first time, before the quiz and its clock start', async () => {
    localStorage.clear()
    const first = mountWithPlugins(TriviaGameView, { attachTo: document.body })
    await flushPromises()
    expect(rulesDialog()).not.toBeNull()
    expect(rulesDialog()!.textContent).toContain('5 întrebări')
    expect(fetchMock).not.toHaveBeenCalled()

    fetchMock.mockResolvedValueOnce(jsonResponse(200, makeGame()))
    clickRulesStart()
    await flushPromises()
    expect(fetchMock.mock.calls[0]![0]).toBe('/api/v1/games/trivia/today/')
    expect(first.find('[data-test="question-card"]').exists()).toBe(true)
    expect(localStorage.getItem('dayzle.trivia.rulesSeen')).toBe('yes')
    first.unmount()
    document.body.innerHTML = ''

    fetchMock.mockResolvedValueOnce(jsonResponse(200, makeGame()))
    const second = mountWithPlugins(TriviaGameView, { attachTo: document.body })
    await flushPromises()
    expect(rulesDialog()).toBeNull()
    second.unmount()
  })

  it('opens the rules again from the rules button', async () => {
    const wrapper = await mountView(jsonResponse(200, makeGame()))
    expect(rulesDialog()).toBeNull()

    await wrapper.find('[data-test="help"]').trigger('click')
    await flushPromises()
    expect(rulesDialog()).not.toBeNull()

    clickRulesStart()
    await flushPromises()
    expect(rulesDialog()).toBeNull()
    expect(fetchMock).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })

  it('keeps the rules button on the result screen', async () => {
    const wrapper = await mountView(jsonResponse(200, finishedGame([true, true, true, true, true])))
    expect(wrapper.find('[data-test="help"]').exists()).toBe(true)
  })
})
