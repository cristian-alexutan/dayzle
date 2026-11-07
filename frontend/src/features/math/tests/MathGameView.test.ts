import { type DOMWrapper, flushPromises, type VueWrapper } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { mountWithPlugins } from '@/tests/utils'

import type { MathGame } from '../types'
import MathGameView from '../views/MathGameView.vue'

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

const game: MathGame = {
  date: '2026-11-07',
  status: 'in_progress',
  target: 253,
  numbers: [1, 2, 2, 25, 50, 100],
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

const tileTexts = (wrapper: VueWrapper) =>
  wrapper.findAll('[data-test="tile"]').map((item) => item.text().replace(/\s+/g, ' ').trim())

/** The first tile showing this number. */
const tile = (wrapper: VueWrapper, text: string) =>
  wrapper.findAll('[data-test="tile"]').find((item) => item.text().trim() === text)!

async function tap(wrapper: VueWrapper, element: DOMWrapper<Element>) {
  await element.trigger('click')
  await flushPromises()
}

async function mountView(firstResponse: Response) {
  fetchMock.mockResolvedValueOnce(firstResponse)
  const wrapper = mountWithPlugins(MathGameView)
  await flushPromises()
  return wrapper
}

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  fetchMock.mockReset()
  vi.unstubAllGlobals()
  vi.useRealTimers()
})

describe('MathGameView', () => {
  it('shows a spinner while the game loads', () => {
    fetchMock.mockReturnValueOnce(new Promise(() => {}))

    const wrapper = mountWithPlugins(MathGameView)

    expect(wrapper.find('[aria-label="Se încarcă jocul"]').exists()).toBe(true)
    wrapper.unmount()
  })

  it('shows the target and every starting number, repeats included', async () => {
    const wrapper = await mountView(jsonResponse(200, game))

    expect(wrapper.find('h1').text()).toBe('Numărăl')
    expect(wrapper.find('[data-test="subtitle"]').text()).toBe(
      'Puzzle-ul zilei · sâmbătă, 7 noiembrie',
    )
    expect(wrapper.find('[data-test="target"]').attributes('aria-label')).toBe('Ținta: 253')
    expect(tileTexts(wrapper)).toEqual(['1', '2', '2', '25', '50', '100'])
    wrapper.unmount()
  })

  it('sends a step to the server and shows the board it sends back', async () => {
    const wrapper = await mountView(jsonResponse(200, game))
    const played = { ...game, steps: [{ left: 100, op: '*', right: 2, result: 200 }] }
    fetchMock.mockResolvedValueOnce(jsonResponse(200, played))

    await tap(wrapper, tile(wrapper, '100'))
    await tap(wrapper, wrapper.find('[data-test="operator-multiply"]'))
    await tap(wrapper, tile(wrapper, '2'))

    const [url, init] = fetchMock.mock.calls[1]!
    expect(url).toBe('/api/v1/games/math/today/progress/')
    expect(JSON.parse(init.body)).toEqual({ steps: [{ left: 100, op: '*', right: 2 }] })
    const labels = wrapper
      .findAll('[data-test="tile"]')
      .map((item) => item.attributes('aria-label'))
    expect(labels).toEqual(['1', '2', '25', '50', '200, rezultat calculat'])
    wrapper.unmount()
  })

  it('refuses a division that is not exact without asking the server', async () => {
    const wrapper = await mountView(jsonResponse(200, game))

    await tap(wrapper, tile(wrapper, '25'))
    await tap(wrapper, wrapper.find('[data-test="operator-divide"]'))
    await tap(wrapper, tile(wrapper, '2'))

    expect(wrapper.find('[data-test="refusal"]').text()).toBe(
      'Împărțirea trebuie să fie exactă: 25 ÷ 2 nu dă un număr întreg.',
    )
    expect(tile(wrapper, '2').classes()).toContain('number-tile--refused')
    expect(fetchMock).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })

  it('shakes the refused tile again on a second refusal right after the first', async () => {
    const wrapper = await mountView(jsonResponse(200, game))

    await tap(wrapper, tile(wrapper, '25'))
    await tap(wrapper, wrapper.find('[data-test="operator-divide"]'))
    await tap(wrapper, tile(wrapper, '2'))
    expect(tile(wrapper, '2').classes()).toContain('number-tile--shake-odd')

    await tap(wrapper, tile(wrapper, '2'))
    expect(tile(wrapper, '2').classes()).toContain('number-tile--shake-even')
    expect(tile(wrapper, '2').classes()).not.toContain('number-tile--shake-odd')
    wrapper.unmount()
  })

  it('shows the score and locks the board when a step reaches the target', async () => {
    const wrapper = await mountView(jsonResponse(200, game))
    const steps = [
      { left: 100, op: '*', right: 2, result: 200 },
      { left: 50, op: '+', right: 2, result: 52 },
      { left: 200, op: '+', right: 52, result: 252 },
      { left: 252, op: '+', right: 1, result: 253 },
    ]
    fetchMock.mockResolvedValueOnce(
      jsonResponse(200, { ...game, status: 'completed', steps, score: 1000, solved: true }),
    )

    await tap(wrapper, tile(wrapper, '100'))
    await tap(wrapper, wrapper.find('[data-test="operator-multiply"]'))
    await tap(wrapper, tile(wrapper, '2'))

    expect(wrapper.find('[data-test="finished"]').text()).toContain('Ai terminat! Scor: 1000')
    expect(
      wrapper.findAll('[data-test="tile"]').every((t) => t.attributes('disabled') !== undefined),
    ).toBe(true)
    wrapper.unmount()
  })

  it('says so when the server refuses a step', async () => {
    const wrapper = await mountView(jsonResponse(200, game))
    fetchMock.mockResolvedValueOnce(errorResponse(400, 'invalid_step'))
    fetchMock.mockResolvedValueOnce(jsonResponse(200, game))

    await tap(wrapper, tile(wrapper, '50'))
    await tap(wrapper, wrapper.find('[data-test="operator-add"]'))
    await tap(wrapper, tile(wrapper, '1'))

    expect(wrapper.find('[data-test="refusal"]').text()).toBe(
      'Pasul nu a putut fi jucat. Încearcă altul.',
    )
    expect(tileTexts(wrapper)).toEqual(['1', '2', '2', '25', '50', '100'])
    // The board didn't change, so the picks stay for another try.
    expect(tile(wrapper, '50').attributes('aria-pressed')).toBe('true')
    wrapper.unmount()
  })

  it('reloads the board after a refused save, so the next step builds on the saved steps', async () => {
    const wrapper = await mountView(jsonResponse(200, game))
    // Another tab already played 100 × 2, so this tab's board is behind.
    const elsewhere = { ...game, steps: [{ left: 100, op: '*', right: 2, result: 200 }] }
    fetchMock.mockResolvedValueOnce(errorResponse(400, 'invalid_step'))
    fetchMock.mockResolvedValueOnce(jsonResponse(200, elsewhere))

    await tap(wrapper, tile(wrapper, '100'))
    await tap(wrapper, wrapper.find('[data-test="operator-add"]'))
    await tap(wrapper, tile(wrapper, '1'))

    expect(fetchMock.mock.calls[2]![0]).toBe('/api/v1/games/math/today/')
    expect(tileTexts(wrapper)).toEqual(['1', '2', '25', '50', 'NOU200'])
    expect(wrapper.find('[data-test="refusal"]').exists()).toBe(true)

    fetchMock.mockResolvedValueOnce(jsonResponse(200, elsewhere))
    await tap(wrapper, tile(wrapper, '50'))
    await tap(wrapper, wrapper.find('[data-test="operator-add"]'))
    await tap(wrapper, tile(wrapper, '1'))

    expect(JSON.parse(fetchMock.mock.calls[3]![1].body)).toEqual({
      steps: [
        { left: 100, op: '*', right: 2 },
        { left: 50, op: '+', right: 1 },
      ],
    })
    wrapper.unmount()
  })

  it('shows the finished game when it was finished in another tab', async () => {
    const wrapper = await mountView(jsonResponse(200, game))
    fetchMock.mockResolvedValueOnce(errorResponse(409, 'already_played'))
    fetchMock.mockResolvedValueOnce(jsonResponse(200, { ...game, status: 'completed', score: 900 }))

    await tap(wrapper, tile(wrapper, '50'))
    await tap(wrapper, wrapper.find('[data-test="operator-add"]'))
    await tap(wrapper, tile(wrapper, '1'))

    expect(wrapper.find('[data-test="finished"]').text()).toContain('Scor: 900')
    expect(wrapper.find('[data-test="refusal"]').exists()).toBe(false)
    wrapper.unmount()
  })

  it('says when there is no puzzle today', async () => {
    const wrapper = await mountView(errorResponse(404, 'no_puzzle'))

    expect(wrapper.find('[data-test="no-puzzle"]').text()).toContain('Revino mâine')
    expect(wrapper.find('button').exists()).toBe(false)
    wrapper.unmount()
  })

  it('sends heartbeats while in progress and none once the game is finished', async () => {
    vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval'] })
    const wrapper = await mountView(jsonResponse(200, game))
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }))

    vi.advanceTimersByTime(15_000)
    expect(fetchMock.mock.calls[1]![0]).toBe('/api/v1/results/math/today/heartbeat/')
    wrapper.unmount()

    fetchMock.mockClear()
    const finished = await mountView(jsonResponse(200, { ...game, status: 'completed' }))
    fetchMock.mockClear()
    vi.advanceTimersByTime(30_000)
    expect(fetchMock).not.toHaveBeenCalled()
    finished.unmount()
  })

  it('offers a retry after another error, and loads the game on retry', async () => {
    const wrapper = await mountView(errorResponse(500, 'server_error'))
    expect(wrapper.text()).toContain('Ceva nu a mers')

    fetchMock.mockResolvedValueOnce(jsonResponse(200, game))
    await wrapper.find('button').trigger('click')
    await flushPromises()

    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(wrapper.find('[data-test="target"]').exists()).toBe(true)
    wrapper.unmount()
  })
})
