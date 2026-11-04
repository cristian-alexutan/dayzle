import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { mountWithPlugins } from '@/tests/utils'

import type { WordGame } from '../types'
import WordGameView from '../views/WordGameView.vue'

const fetchMock = vi.fn()

function jsonResponse(body: unknown) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })
}

const guess = { word: 'tunel', colors: ['absent', 'absent', 'absent', 'absent', 'absent'] }

function makeGame(overrides: Partial<WordGame> = {}) {
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

const solvedGame = makeGame({
  status: 'completed',
  guesses: [guess, guess, guess] as WordGame['guesses'],
  answer: 'carte',
  solved: true,
  score: 4,
  duration_ms: 65_000,
})

const dialogText = () => document.querySelector('[role="dialog"]')?.textContent ?? null

async function mountView(game: unknown) {
  fetchMock.mockResolvedValueOnce(jsonResponse(game))
  const wrapper = mountWithPlugins(WordGameView, { attachTo: document.body })
  await flushPromises()
  return wrapper
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  fetchMock.mockReset()
  vi.unstubAllGlobals()
  vi.useRealTimers()
  document.body.innerHTML = ''
})

describe('Word game result', () => {
  it('opens right away when a finished game loads, with the result, word and time', async () => {
    const wrapper = await mountView(solvedGame)

    vi.advanceTimersByTime(0)
    await flushPromises()

    const text = dialogText()
    expect(text).toContain('Felicitări!')
    expect(text).toContain('3/6')
    expect(text).toContain('carte')
    expect(text).toContain('1:05')
    wrapper.unmount()
  })

  it('shows X/6 for a failed game', async () => {
    const wrapper = await mountView(
      makeGame({ status: 'completed', answer: 'carte', solved: false, duration_ms: 1000 }),
    )

    vi.advanceTimersByTime(0)
    await flushPromises()

    expect(dialogText()).toContain('X/6')
    wrapper.unmount()
  })

  it('shows the word in tiles: green when solved, accent when failed', async () => {
    const solved = await mountView(solvedGame)
    vi.advanceTimersByTime(0)
    await flushPromises()
    const solvedTiles = document.querySelectorAll('[data-test="answer-tile"]')
    expect(solvedTiles).toHaveLength(5)
    expect(solvedTiles[0]!.classList).toContain('word-tile--correct')
    solved.unmount()

    const failed = await mountView(
      makeGame({ status: 'completed', answer: 'câine', solved: false, duration_ms: 1000 }),
    )
    vi.advanceTimersByTime(0)
    await flushPromises()
    const failedTiles = document.querySelectorAll('[data-test="answer-tile"]')
    expect(failedTiles[1]!.textContent?.trim()).toBe('â')
    expect(failedTiles[1]!.classList).toContain('word-tile--accent')
    failed.unmount()
  })

  it('waits for the flip when the player has just finished', async () => {
    const wrapper = await mountView(makeGame())
    fetchMock.mockResolvedValueOnce(jsonResponse(solvedGame))

    for (const key of 'carte') window.dispatchEvent(new KeyboardEvent('keydown', { key }))
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', cancelable: true }))
    await flushPromises()
    expect(dialogText()).toBeNull()

    vi.advanceTimersByTime(1500)
    await flushPromises()
    expect(dialogText()).toContain('3/6')
    wrapper.unmount()
  })

  it('can be reopened from a button after closing it', async () => {
    const wrapper = await mountView(solvedGame)
    expect(wrapper.find('[data-test="enter"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="see-result"]').exists()).toBe(true)

    vi.advanceTimersByTime(0)
    await flushPromises()
    expect(wrapper.find('[data-test="see-result"]').exists()).toBe(false)

    document.querySelector<HTMLElement>('[role="dialog"] button')!.click()
    await flushPromises()
    expect(wrapper.find('[data-test="see-result"]').exists()).toBe(true)

    await wrapper.find('[data-test="see-result"]').trigger('click')
    await flushPromises()
    expect(dialogText()).toContain('3/6')
    wrapper.unmount()
  })
})
