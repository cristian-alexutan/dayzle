import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h } from 'vue'

import { mountWithPlugins } from '@/tests/utils'

import { useAnswerMutation, useTriviaGameQuery } from '../api/queries'
import { answerTo, jsonResponse, makeGame } from './fixtures'

const fetchMock = vi.fn()

function mountHooks() {
  let hooks!: {
    game: ReturnType<typeof useTriviaGameQuery>
    answer: ReturnType<typeof useAnswerMutation>
  }
  mountWithPlugins(
    defineComponent({
      setup() {
        hooks = { game: useTriviaGameQuery('today'), answer: useAnswerMutation('today') }
        return () => h('div')
      },
    }),
  )
  return hooks
}

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  fetchMock.mockReset()
  vi.unstubAllGlobals()
})

describe('trivia queries', () => {
  it('loads the quiz of the day', async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, makeGame()))

    const { game } = mountHooks()
    await flushPromises()

    expect(fetchMock).toHaveBeenCalledWith('/api/v1/games/trivia/today/', expect.anything())
    expect(game.data.value?.questions).toHaveLength(5)
  })

  it('replaces the cached quiz with the one the answer returns', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(200, makeGame()))
    const { game, answer } = mountHooks()
    await flushPromises()

    fetchMock.mockResolvedValueOnce(jsonResponse(200, makeGame({ answers: [answerTo(1, true)] })))
    await answer.mutateAsync({ question: 1, choice: 11 })
    await flushPromises()

    const [url, init] = fetchMock.mock.calls[1]!
    expect(url).toBe('/api/v1/games/trivia/today/answer/')
    expect(init.method).toBe('POST')
    expect(game.data.value?.answers).toEqual([answerTo(1, true)])
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('keeps the answer when a reload started before it finishes after it', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(200, makeGame()))
    const { game, answer } = mountHooks()
    await flushPromises()

    // A reload (window focus) is on its way with the quiz as it was before the answer.
    let finishReload!: (response: Response) => void
    fetchMock.mockReturnValueOnce(new Promise<Response>((resolve) => (finishReload = resolve)))
    void game.refetch()
    await flushPromises()

    fetchMock.mockResolvedValueOnce(jsonResponse(200, makeGame({ answers: [answerTo(1, true)] })))
    await answer.mutateAsync({ question: 1, choice: 11 })
    finishReload(jsonResponse(200, makeGame()))
    await flushPromises()

    expect(game.data.value?.answers).toEqual([answerTo(1, true)])
  })

  it('keeps the answer when a reload starts while it is on its way', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(200, makeGame()))
    const { game, answer } = mountHooks()
    await flushPromises()

    let finishAnswer!: (response: Response) => void
    fetchMock.mockReturnValueOnce(new Promise<Response>((resolve) => (finishAnswer = resolve)))
    const answered = answer.mutateAsync({ question: 1, choice: 11 })
    await flushPromises()

    let finishReload!: (response: Response) => void
    fetchMock.mockReturnValueOnce(new Promise<Response>((resolve) => (finishReload = resolve)))
    void game.refetch()
    await flushPromises()

    finishAnswer(jsonResponse(200, makeGame({ answers: [answerTo(1, true)] })))
    await answered
    finishReload(jsonResponse(200, makeGame()))
    await flushPromises()

    expect(game.data.value?.answers).toEqual([answerTo(1, true)])
  })
})
