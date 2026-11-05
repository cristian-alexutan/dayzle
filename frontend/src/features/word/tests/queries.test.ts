import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h } from 'vue'

import { mountWithPlugins } from '@/tests/utils'

import { useGuessMutation, useWordGameQuery } from '../api/queries'

const fetchMock = vi.fn()

function jsonResponse(body: unknown) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })
}

const emptyGame = {
  date: '2026-11-04',
  status: 'in_progress',
  word_length: 5,
  max_attempts: 6,
  guesses: [],
  answer: null,
  solved: null,
  score: null,
  duration_ms: null,
}

function mountHooks() {
  let hooks!: {
    game: ReturnType<typeof useWordGameQuery>
    guess: ReturnType<typeof useGuessMutation>
  }
  mountWithPlugins(
    defineComponent({
      setup() {
        hooks = { game: useWordGameQuery('today'), guess: useGuessMutation('today') }
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

describe('word queries', () => {
  it('loads the game of the day', async () => {
    fetchMock.mockResolvedValue(jsonResponse(emptyGame))

    const { game } = mountHooks()
    await flushPromises()

    expect(fetchMock.mock.calls[0]![0]).toBe('/api/v1/games/word/today/')
    expect(game.data.value?.status).toBe('in_progress')
  })

  it('posts a guess and replaces the cached game with the response', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(emptyGame))
    const { game, guess } = mountHooks()
    await flushPromises()

    const updated = {
      ...emptyGame,
      guesses: [{ word: 'tunel', colors: ['absent', 'absent', 'absent', 'absent', 'absent'] }],
    }
    fetchMock.mockResolvedValueOnce(jsonResponse(updated))
    await guess.mutateAsync('tunel')

    const [url, init] = fetchMock.mock.calls[1]!
    expect(url).toBe('/api/v1/games/word/today/guess/')
    expect(init.body).toBe(JSON.stringify({ guess: 'tunel' }))
    expect(game.data.value?.guesses).toEqual(updated.guesses)
  })
})
