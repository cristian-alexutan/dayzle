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
    hints: [],
    hint_penalty: 2,
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

/** Close the rules that open with an unfinished game, so tests can play. */
async function closeRules() {
  document.body.querySelector<HTMLElement>('[data-test="how-to-play-close"]')?.click()
  await flushPromises()
}

async function mountView(firstResponse: Response, { keepRules = false } = {}) {
  fetchMock.mockResolvedValueOnce(firstResponse)
  const wrapper = mountWithPlugins(WordGameView, { attachTo: document.body })
  await flushPromises()
  if (!keepRules) await closeRules()
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
    // Only the rules button stays; there is nothing to retry or hint.
    const buttons = wrapper.findAll('button')
    expect(buttons.map((button) => button.attributes('data-test'))).toEqual(['how-to-play'])
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

  it('takes a hint and shows the revealed letter on a tile and the keyboard', async () => {
    const wrapper = await mountView(jsonResponse(200, makeGame()))
    expect(wrapper.find('[data-test="hint"]').text()).toBe('Indiciu')
    fetchMock.mockResolvedValueOnce(jsonResponse(200, makeGame({ hints: ['c'] })))

    await wrapper.find('[data-test="hint"]').trigger('click')
    await flushPromises()

    const [url, init] = fetchMock.mock.calls[1]!
    expect(url).toBe('/api/v1/games/word/today/hint/')
    expect(init.method).toBe('POST')
    expect(wrapper.find('[data-test="hint-letters"]').text()).toBe('c')
    expect(wrapper.find('[data-test="key-c"]').classes()).toContain('word-keyboard__key--present')
    wrapper.unmount()
  })

  it('says the player has every letter when there is nothing left to hint', async () => {
    const wrapper = await mountView(jsonResponse(200, makeGame()))
    fetchMock.mockResolvedValueOnce(errorResponse(409, 'nothing_to_hint'))

    await wrapper.find('[data-test="hint"]').trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-test="hint-notice"]').text()).toBe(
      'Ai toate literele. Poți s-o faci!',
    )
    expect(wrapper.find('[data-test="rejection"]').exists()).toBe(false)
    wrapper.unmount()
  })

  it('has no hint button once the game is finished', async () => {
    const wrapper = await mountView(
      jsonResponse(200, makeGame({ status: 'completed', answer: 'carte', hints: ['c'] })),
    )

    expect(wrapper.find('[data-test="hint"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="hint-letters"]').exists()).toBe(true)
    wrapper.unmount()
  })

  it('opens the rules every time an unfinished game is opened', async () => {
    for (const guesses of [[], [tunel]]) {
      const wrapper = await mountView(jsonResponse(200, makeGame({ guesses })), {
        keepRules: true,
      })

      const rules = document.body.querySelector('[data-test="how-to-play-rules"]')
      expect(rules?.textContent).toContain('Fiecare indiciu costă 2 puncte')
      wrapper.unmount()
      document.body.innerHTML = ''
    }
  })

  it('ignores typing while the rules are open', async () => {
    const wrapper = await mountView(jsonResponse(200, makeGame()), { keepRules: true })

    typeWord('carte')
    pressEnter()
    await flushPromises()

    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(wrapper.findAll('[data-test="tile"]')[0]!.text()).toBe('')
    wrapper.unmount()
  })

  it('pauses the clock while the rules are open', async () => {
    vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval'] })
    const wrapper = await mountView(jsonResponse(200, makeGame()), { keepRules: true })
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }))

    vi.advanceTimersByTime(30_000)
    expect(fetchMock).toHaveBeenCalledTimes(1)

    await closeRules()
    vi.advanceTimersByTime(15_000)
    expect(fetchMock.mock.calls[1]![0]).toBe('/api/v1/results/word/today/heartbeat/')
    wrapper.unmount()
  })

  it('shows only the result, not the rules, when the game is already finished', async () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    const wrapper = await mountView(
      jsonResponse(200, makeGame({ status: 'completed', answer: 'carte', solved: true })),
      { keepRules: true },
    )
    vi.advanceTimersByTime(0)
    await flushPromises()

    expect(document.body.querySelector('[data-test="how-to-play-rules"]')).toBeNull()
    expect(document.body.querySelector('[data-test="answer"]')).not.toBeNull()
    wrapper.unmount()
  })

  it('opens the rules from the info button, also once the game is finished', async () => {
    const wrapper = await mountView(
      jsonResponse(200, makeGame({ status: 'completed', answer: 'carte' })),
    )
    expect(document.body.querySelector('[data-test="how-to-play-rules"]')).toBeNull()

    await wrapper.find('[data-test="how-to-play"]').trigger('click')
    await flushPromises()

    expect(document.body.querySelector('[data-test="how-to-play-rules"]')).not.toBeNull()
    wrapper.unmount()
  })
})
