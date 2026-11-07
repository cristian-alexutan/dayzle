import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h } from 'vue'

import { mountWithPlugins } from '@/tests/utils'

import {
  errorCode,
  useMathGameQuery,
  useSaveProgressMutation,
  useSubmitMutation,
} from '../api/queries'
import type { MathGame, PlayedStep } from '../types'

const fetchMock = vi.fn()

function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const newGame: MathGame = {
  date: '2026-11-07',
  status: 'in_progress',
  target: 253,
  numbers: [1, 2, 3, 25, 50, 100],
  max_steps: 5,
  steps: [],
  final_result: null,
  distance: null,
  operations: null,
  solved: null,
  score: null,
  duration_ms: null,
  solution: null,
  min_operations: null,
  difficulty: null,
}

const solvedSteps: PlayedStep[] = [
  { left: 100, op: '*', right: 2, result: 200 },
  { left: 50, op: '+', right: 3, result: 53 },
  { left: 200, op: '+', right: 53, result: 253 },
]

const finishedGame: MathGame = {
  ...newGame,
  status: 'completed',
  steps: solvedSteps,
  final_result: 253,
  distance: 0,
  operations: 3,
  solved: true,
  score: 1000,
  duration_ms: 42000,
  solution: solvedSteps,
  min_operations: 3,
  difficulty: 'easy',
}

function mountHooks() {
  let hooks!: {
    game: ReturnType<typeof useMathGameQuery>
    save: ReturnType<typeof useSaveProgressMutation>
    submit: ReturnType<typeof useSubmitMutation>
  }
  mountWithPlugins(
    defineComponent({
      setup() {
        hooks = {
          game: useMathGameQuery('today'),
          save: useSaveProgressMutation('today'),
          submit: useSubmitMutation('today'),
        }
        return () => h('div')
      },
    }),
  )
  return hooks
}

async function mountLoaded() {
  fetchMock.mockResolvedValueOnce(jsonResponse(200, newGame))
  const hooks = mountHooks()
  await flushPromises()
  return hooks
}

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  fetchMock.mockReset()
  vi.unstubAllGlobals()
})

describe('math queries', () => {
  it('loads the game of the day', async () => {
    const { game } = await mountLoaded()

    expect(fetchMock.mock.calls[0]![0]).toBe('/api/v1/games/math/today/')
    expect(game.data.value?.target).toBe(253)
  })

  it('saves the steps without the results the browser computed', async () => {
    const { game, save } = await mountLoaded()
    const saved = { ...newGame, steps: [solvedSteps[0]!] }
    fetchMock.mockResolvedValueOnce(jsonResponse(200, saved))

    await save.mutateAsync([solvedSteps[0]!])

    const [url, init] = fetchMock.mock.calls[1]!
    expect(url).toBe('/api/v1/games/math/today/progress/')
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body)).toEqual({ steps: [{ left: 100, op: '*', right: 2 }] })
    expect(game.data.value?.steps).toEqual(saved.steps)
  })

  it('shows the finished game when a saved step reaches the target', async () => {
    const { game, save } = await mountLoaded()
    fetchMock.mockResolvedValueOnce(jsonResponse(200, finishedGame))

    await save.mutateAsync(solvedSteps)

    expect(game.data.value?.status).toBe('completed')
    expect(game.data.value?.score).toBe(1000)
  })

  it('submits the steps and replaces the cached game with the result', async () => {
    const { game, submit } = await mountLoaded()
    fetchMock.mockResolvedValueOnce(jsonResponse(200, finishedGame))

    await submit.mutateAsync(solvedSteps)

    expect(fetchMock.mock.calls[1]![0]).toBe('/api/v1/games/math/today/submit/')
    expect(game.data.value?.solution).toEqual(solvedSteps)
  })

  it('keeps the cached board when a step is refused', async () => {
    const { game, save } = await mountLoaded()
    const refused = { error: { code: 'invalid_step', message: 'No', details: { step: 0 } } }
    fetchMock.mockResolvedValueOnce(jsonResponse(400, refused))

    const error = await save
      .mutateAsync([{ left: 7, op: '+', right: 1 }])
      .catch((caught: unknown) => caught)

    expect(errorCode(error)).toBe('invalid_step')
    expect(game.data.value).toEqual(newGame)
  })
})

describe('errorCode', () => {
  it('is null for errors that did not come from the backend', () => {
    expect(errorCode(new Error('offline'))).toBeNull()
  })
})
