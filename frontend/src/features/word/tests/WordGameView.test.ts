import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { mountWithPlugins } from '@/tests/utils'

import type { WordGame } from '../types'
import WordGameView from '../views/WordGameView.vue'

const fetchMock = vi.fn()

function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function errorResponse(status: number, code: string) {
  return jsonResponse(status, { error: { code, message: code, details: null } })
}

function makeGame(overrides: Partial<WordGame> = {}): WordGame {
  return {
    date: '2026-11-04',
    status: 'in_progress',
    word_length: 5,
    max_attempts: 6,
    guesses: [],
    answer: null,
    solved: null,
    score: null,
    duration_ms: null,
    ...overrides,
  }
}

const tunel = {
  word: 'tunel',
  colors: ['present', 'absent', 'absent', 'present', 'absent'],
} as WordGame['guesses'][number]

async function mountView(firstResponse: Response) {
  fetchMock.mockResolvedValueOnce(firstResponse)
  const wrapper = mountWithPlugins(WordGameView, { attachTo: document.body })
  await flushPromises()
  return wrapper
}

function typeWord(word: string) {
  for (const key of Array.from(word)) window.dispatchEvent(new KeyboardEvent('keydown', { key }))
}

function pressEnter() {
  window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', cancelable: true }))
}

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  fetchMock.mockReset()
  vi.unstubAllGlobals()
  vi.useRealTimers()
  document.body.innerHTML = ''
})

describe('WordGameView', () => {
  it('restores the board from the server state', async () => {
    const wrapper = await mountView(jsonResponse(200, makeGame({ guesses: [tunel] })))

    const tiles = wrapper.findAll('[data-test="tile"]')
    expect(tiles[0]!.text()).toBe('t')
    expect(tiles[0]!.classes()).toContain('word-tile--present')
    expect(tiles[0]!.classes()).not.toContain('word-board__tile--reveal')
    wrapper.unmount()
  })

  it('sends a typed guess, shows its colors and clears the input', async () => {
    const wrapper = await mountView(jsonResponse(200, makeGame()))
    fetchMock.mockResolvedValueOnce(jsonResponse(200, makeGame({ guesses: [tunel] })))

    typeWord('tunel')
    pressEnter()
    await flushPromises()

    const [url, init] = fetchMock.mock.calls[1]!
    expect(url).toBe('/api/v1/games/word/today/guess/')
    expect(init.body).toBe(JSON.stringify({ guess: 'tunel' }))
    const tiles = wrapper.findAll('[data-test="tile"]')
    expect(tiles[0]!.classes()).toContain('word-board__tile--reveal')
    expect(tiles[5]!.text()).toBe('')
    wrapper.unmount()
  })

  it('rejects a word not in the list, keeping the letters and shaking the row', async () => {
    const wrapper = await mountView(jsonResponse(200, makeGame()))
    fetchMock.mockResolvedValueOnce(errorResponse(400, 'not_a_word'))

    typeWord('zzzzz')
    pressEnter()
    await flushPromises()

    expect(wrapper.find('[data-test="rejection"]').text()).toContain('Cuvântul nu este în listă')
    expect(wrapper.findAll('[data-test="row"]')[0]!.classes()).toContain('word-board__row--shake')
    expect(wrapper.findAll('[data-test="tile"]')[0]!.text()).toBe('z')
    wrapper.unmount()
  })

  it('rejects a short word without calling the server', async () => {
    const wrapper = await mountView(jsonResponse(200, makeGame()))

    typeWord('car')
    pressEnter()
    await flushPromises()

    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(wrapper.find('[data-test="rejection"]').exists()).toBe(true)
    wrapper.unmount()
  })

  it('hides the rejection message after a moment', async () => {
    const wrapper = await mountView(jsonResponse(200, makeGame()))
    vi.useFakeTimers()

    typeWord('car')
    pressEnter()
    await wrapper.vm.$nextTick()
    expect(wrapper.find('[data-test="rejection"]').exists()).toBe(true)

    vi.advanceTimersByTime(2000)
    await wrapper.vm.$nextTick()

    expect(wrapper.find('[data-test="rejection"]').exists()).toBe(false)
    wrapper.unmount()
  })

  it('reloads the game when it was already finished elsewhere', async () => {
    const wrapper = await mountView(jsonResponse(200, makeGame()))
    fetchMock.mockResolvedValueOnce(errorResponse(409, 'already_played'))
    fetchMock.mockResolvedValueOnce(
      jsonResponse(200, makeGame({ status: 'completed', guesses: [tunel], answer: 'carte' })),
    )

    typeWord('tunel')
    pressEnter()
    await flushPromises()

    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(wrapper.find('[data-test="rejection"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="enter"]').exists()).toBe(false)
    wrapper.unmount()
  })

  it('shows "no puzzle today" without a retry button', async () => {
    const wrapper = await mountView(errorResponse(404, 'no_puzzle'))

    expect(wrapper.find('[data-test="no-puzzle"]').exists()).toBe(true)
    expect(wrapper.find('button').exists()).toBe(false)
    wrapper.unmount()
  })

  it('sends heartbeats while in progress and none once the game is finished', async () => {
    vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval'] })
    const wrapper = await mountView(jsonResponse(200, makeGame()))
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }))

    vi.advanceTimersByTime(15_000)
    expect(fetchMock.mock.calls[1]![0]).toBe('/api/v1/results/word/today/heartbeat/')
    wrapper.unmount()

    fetchMock.mockClear()
    const finished = await mountView(jsonResponse(200, makeGame({ status: 'completed' })))
    fetchMock.mockClear()
    vi.advanceTimersByTime(30_000)
    expect(fetchMock).not.toHaveBeenCalled()
    finished.unmount()
  })
})
