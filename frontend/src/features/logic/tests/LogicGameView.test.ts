import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { mountWithPlugins } from '@/tests/utils'

import type { CellResult, LogicGame } from '../types'
import LogicGameView from '../views/LogicGameView.vue'
import { makeGame } from './fixtures'

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

function cellResult(game: LogicGame, conflicts: CellResult['conflicts'] = []) {
  return jsonResponse(200, { rejected: conflicts.length > 0, conflicts, game })
}

/** A response that only arrives when the test says so. */
function deferred() {
  let resolve!: (response: Response) => void
  const promise = new Promise<Response>((r) => (resolve = r))
  return { promise, resolve }
}

async function mountView(firstResponse?: Response) {
  if (firstResponse) fetchMock.mockResolvedValueOnce(firstResponse)
  const wrapper = mountWithPlugins(LogicGameView, { attachTo: document.body })
  await flushPromises()
  return wrapper
}

function requestsTo(path: string) {
  return fetchMock.mock.calls.filter(([url]) => String(url).endsWith(path))
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

  it('sends each tap as a cell change and shows it right away', async () => {
    const wrapper = await mountView(jsonResponse(200, makeGame()))
    const cell = () => wrapper.findAll('[data-test="cell"]')[1]!
    const pending = deferred()
    fetchMock.mockReturnValueOnce(pending.promise)

    await cell().trigger('click')
    await flushPromises()

    // On screen while the server hasn't answered yet.
    expect(cell().find('.pi-times').exists()).toBe(true)
    const [, init] = requestsTo('/cell/')[0]!
    expect(JSON.parse(init.body)).toEqual({ row: 0, col: 1, content: 'mark' })

    pending.resolve(cellResult(makeGame({ marks: [[0, 1]] })))
    await flushPromises()
    expect(cell().find('.pi-times').exists()).toBe(true)
    wrapper.unmount()
  })

  it('sends quick taps one at a time and in order, without losing any', async () => {
    const wrapper = await mountView(jsonResponse(200, makeGame()))
    const cells = () => wrapper.findAll('[data-test="cell"]')
    const first = deferred()
    fetchMock.mockReturnValueOnce(first.promise)
    fetchMock.mockResolvedValueOnce(
      cellResult(
        makeGame({
          marks: [
            [0, 0],
            [1, 1],
          ],
        }),
      ),
    )

    await cells()[0]!.trigger('click')
    await cells()[3]!.trigger('click')
    expect(requestsTo('/cell/')).toHaveLength(1) // the second waits for the first

    first.resolve(cellResult(makeGame({ marks: [[0, 0]] })))
    await flushPromises()

    expect(requestsTo('/cell/')).toHaveLength(2)
    expect(cells()[0]!.find('.pi-times').exists()).toBe(true)
    expect(cells()[3]!.find('.pi-times').exists()).toBe(true)
    wrapper.unmount()
  })

  it('shows a rejected sun in red with its conflicts, then removes it', async () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    const start = makeGame({ suns: [[0, 0]], marks: [[1, 0]] })
    const wrapper = await mountView(jsonResponse(200, start))
    const cells = () => wrapper.findAll('[data-test="cell"]')

    fetchMock.mockResolvedValueOnce(cellResult({ ...start, mistakes: 1 }, [[0, 0]]))
    await cells()[2]!.trigger('click') // the X on (1, 0) becomes a sun
    await flushPromises()

    expect(cells()[2]!.classes()).toContain('logic-cell--rejected')
    expect(cells()[0]!.classes()).toContain('logic-cell--conflict')
    expect(wrapper.find('[data-test="mistakes"]').text()).toContain('1')

    await vi.runOnlyPendingTimersAsync()
    expect(cells()[2]!.classes()).not.toContain('logic-cell--rejected')
    expect(cells()[2]!.find('.pi-times').exists()).toBe(true)
    wrapper.unmount()
  })

  it('loads the real board again when a change fails', async () => {
    const wrapper = await mountView(jsonResponse(200, makeGame()))
    fetchMock.mockResolvedValueOnce(errorResponse(500, 'server_error'))
    fetchMock.mockResolvedValueOnce(jsonResponse(200, makeGame()))

    await wrapper.findAll('[data-test="cell"]')[0]!.trigger('click')
    await flushPromises()

    expect(wrapper.findAll('[data-test="cell"]')[0]!.find('.pi-times').exists()).toBe(false)
    expect(wrapper.find('[data-test="error"]').exists()).toBe(true)
    wrapper.unmount()
  })

  it('undoes the last change and clears the board', async () => {
    const wrapper = await mountView(jsonResponse(200, makeGame()))
    const cells = () => wrapper.findAll('[data-test="cell"]')
    fetchMock.mockImplementation(async (url: string, init: RequestInit) => {
      if (url.endsWith('/clear/')) return jsonResponse(200, makeGame())
      const { row, col, content } = JSON.parse(String(init.body))
      return cellResult(makeGame(content === 'mark' ? { marks: [[row, col]] } : {}))
    })

    await cells()[0]!.trigger('click')
    await flushPromises()
    await wrapper.find('[data-test="undo"]').trigger('click')
    await flushPromises()
    const cellRequests = requestsTo('/cell/')
    expect(JSON.parse(cellRequests[cellRequests.length - 1]![1].body).content).toBe('empty')
    expect(cells()[0]!.find('.pi-times').exists()).toBe(false)

    await cells()[0]!.trigger('click')
    await flushPromises()
    await wrapper.find('[data-test="clear"]').trigger('click')
    await flushPromises()
    expect(requestsTo('/clear/')).toHaveLength(1)
    expect(cells()[0]!.find('.pi-times').exists()).toBe(false)
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

  it('opens the rules before loading the game the first time, and not again', async () => {
    localStorage.clear()
    const first = await mountView()
    expect(document.body.querySelector('[data-test="tutorial"]')).not.toBeNull()
    expect(fetchMock).not.toHaveBeenCalled() // the clock hasn't started

    fetchMock.mockResolvedValueOnce(jsonResponse(200, makeGame()))
    ;(document.body.querySelector('[data-test="tutorial-start"]') as HTMLElement).click()
    await flushPromises()
    expect(requestsTo('/games/logic/today/')).toHaveLength(1)
    first.unmount()
    document.body.innerHTML = ''

    const second = await mountView(jsonResponse(200, makeGame()))
    expect(document.body.querySelector('[data-test="tutorial"]')).toBeNull()
    second.unmount()
  })

  it('shows a message when there is no puzzle today', async () => {
    const wrapper = await mountView(errorResponse(404, 'no_puzzle'))

    expect(wrapper.find('[data-test="no-puzzle"]').exists()).toBe(true)
    wrapper.unmount()
  })
})
