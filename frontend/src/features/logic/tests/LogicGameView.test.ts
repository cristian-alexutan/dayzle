import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { mountWithPlugins } from '@/tests/utils'

import type { LogicGame, PlaceResult } from '../types'
import LogicGameView from '../views/LogicGameView.vue'

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

function makeGame(overrides: Partial<LogicGame> = {}): LogicGame {
  return {
    date: '2026-11-05',
    status: 'in_progress',
    size: 2,
    regions: [
      [0, 1],
      [0, 1],
    ],
    suns: [],
    marks: [],
    mistakes: 0,
    streak: 0,
    solved: null,
    score: null,
    duration_ms: null,
    elapsed_ms: 0,
    solution: null,
    ...overrides,
  }
}

function placed(correct: boolean, game: LogicGame, conflicts: PlaceResult['conflicts'] = []) {
  return jsonResponse(200, { correct, conflicts, game })
}

async function mountView(firstResponse: Response) {
  fetchMock.mockResolvedValueOnce(firstResponse)
  const wrapper = mountWithPlugins(LogicGameView, { attachTo: document.body })
  await flushPromises()
  return wrapper
}

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock)
  // Most tests are about playing, so the first-time rules dialog stays closed.
  localStorage.setItem('dayzle.logic.tutorialSeen', 'yes')
})

afterEach(() => {
  localStorage.clear()
  fetchMock.mockReset()
  vi.unstubAllGlobals()
  vi.useRealTimers()
  document.body.innerHTML = ''
})

describe('LogicGameView', () => {
  it('shows the grid with the suns and marks from the server', async () => {
    const wrapper = await mountView(
      jsonResponse(200, makeGame({ suns: [[0, 0]], marks: [[1, 1]] })),
    )

    const cells = wrapper.findAll('[data-test="cell"]')
    expect(cells).toHaveLength(4)
    expect(cells[0]!.find('.pi-sun').exists()).toBe(true)
    expect(cells[3]!.find('.pi-times').exists()).toBe(true)
    wrapper.unmount()
  })

  it('marks a cell on the first tap and sends a sun on the second', async () => {
    const wrapper = await mountView(jsonResponse(200, makeGame()))
    const cell = () => wrapper.findAll('[data-test="cell"]')[1]!

    await cell().trigger('click')
    expect(cell().find('.pi-times').exists()).toBe(true)

    fetchMock.mockResolvedValueOnce(placed(true, makeGame({ suns: [[0, 1]], streak: 1 })))
    await cell().trigger('click')
    await flushPromises()

    const [url, init] = fetchMock.mock.lastCall!
    expect(url).toBe('/api/v1/games/logic/today/place/')
    expect(JSON.parse(init.body)).toEqual({ row: 0, col: 1 })
    expect(cell().find('.pi-sun').exists()).toBe(true)
    expect(wrapper.find('[data-test="streak"]').text()).toContain('×1')
    wrapper.unmount()
  })

  it('shows a wrong sun in red with its conflicts, then removes it', async () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    const start = makeGame({ suns: [[0, 0]] })
    const wrapper = await mountView(jsonResponse(200, start))
    const cells = () => wrapper.findAll('[data-test="cell"]')

    fetchMock.mockResolvedValueOnce(placed(false, { ...start, mistakes: 1 }, [[0, 0]]))
    await cells()[2]!.trigger('click')
    await cells()[2]!.trigger('click')
    await flushPromises()

    expect(cells()[2]!.classes()).toContain('logic-cell--wrong')
    expect(cells()[0]!.classes()).toContain('logic-cell--conflict')
    expect(wrapper.find('[data-test="mistakes"]').text()).toContain('1')

    await vi.runOnlyPendingTimersAsync()
    expect(cells()[2]!.classes()).not.toContain('logic-cell--wrong')
    expect(cells()[2]!.find('.pi-sun').exists()).toBe(false)
    wrapper.unmount()
  })

  it('shows the result of a finished game', async () => {
    const finished = makeGame({
      status: 'completed',
      suns: [
        [0, 0],
        [1, 1],
      ],
      mistakes: 2,
      solved: true,
      score: 850,
      duration_ms: 95_000,
      elapsed_ms: 95_000,
    })
    const wrapper = await mountView(jsonResponse(200, finished))

    expect(document.body.textContent).toContain('850/1000')
    const mistakes = document.body.querySelector('[data-test="result-mistakes"]')
    expect(mistakes?.textContent).toContain('2 greșeli')
    wrapper.unmount()
  })

  it('opens the rules the first time, and not again', async () => {
    localStorage.clear()
    const first = await mountView(jsonResponse(200, makeGame()))
    expect(document.body.querySelector('[data-test="tutorial"]')).not.toBeNull()
    first.unmount()
    document.body.innerHTML = ''

    const second = await mountView(jsonResponse(200, makeGame()))
    expect(document.body.querySelector('[data-test="tutorial"]')).toBeNull()

    await second.find('[data-test="help"]').trigger('click')
    expect(document.body.querySelector('[data-test="tutorial"]')).not.toBeNull()
    second.unmount()
  })

  it('undoes and clears X marks from the toolbar', async () => {
    const wrapper = await mountView(jsonResponse(200, makeGame()))
    const cells = () => wrapper.findAll('[data-test="cell"]')
    const undo = () => wrapper.find('[data-test="undo"]')

    expect(undo().attributes('disabled')).toBeDefined()
    await cells()[0]!.trigger('click')
    await cells()[1]!.trigger('click')

    await undo().trigger('click')
    expect(cells()[1]!.find('.pi-times').exists()).toBe(false)
    expect(cells()[0]!.find('.pi-times').exists()).toBe(true)

    await wrapper.find('[data-test="clear"]').trigger('click')
    expect(cells()[0]!.find('.pi-times').exists()).toBe(false)
    wrapper.unmount()
  })

  it('shows a message when there is no puzzle today', async () => {
    const wrapper = await mountView(errorResponse(404, 'no_puzzle'))

    expect(wrapper.find('[data-test="no-puzzle"]').exists()).toBe(true)
    wrapper.unmount()
  })
})
