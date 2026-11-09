import { type DOMWrapper, flushPromises, type VueWrapper } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h, ref } from 'vue'

import { mountWithPlugins } from '@/tests/utils'

import { EGG_MS } from '../composables/useEasterEggs'
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
  document.body.innerHTML = ''
})

/** Let requests answer, then the timer that opens the result. */
async function settle() {
  await flushPromises()
  await new Promise((resolve) => setTimeout(resolve))
}

/** The result dialog's text, or null while it's closed. It's rendered at the end of the page. */
const dialogText = () => document.querySelector('[role="dialog"]')?.textContent ?? null

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

    expect(dialogText()).toContain('Ai nimerit 253!')
    expect(dialogText()).toContain('1000')
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

    expect(dialogText()).toContain('900')
    expect(wrapper.find('[data-test="refusal"]').exists()).toBe(false)
    wrapper.unmount()
  })

  describe('history, closest so far, undo and reset', () => {
    const played = {
      ...game,
      steps: [
        { left: 100, op: '*', right: 2, result: 200 },
        { left: 50, op: '+', right: 2, result: 52 },
      ],
    } satisfies MathGame
    const sentSteps = (call: number) => JSON.parse(fetchMock.mock.calls[call]![1].body).steps
    const button = (wrapper: VueWrapper, name: string) => wrapper.find(`[data-test="${name}"]`)

    it('before the first step: a hint, no closest number, nothing to undo', async () => {
      const wrapper = await mountView(jsonResponse(200, game))

      expect(wrapper.find('[data-test="history-empty"]').exists()).toBe(true)
      expect(wrapper.find('[data-test="closest"]').exists()).toBe(false)
      expect(button(wrapper, 'undo').attributes('disabled')).toBeDefined()
      expect(button(wrapper, 'reset').attributes('disabled')).toBeDefined()
      wrapper.unmount()
    })

    it('lists the saved steps and the computed number closest to the target', async () => {
      const wrapper = await mountView(jsonResponse(200, played))

      expect(wrapper.findAll('[data-test="step"]')).toHaveLength(2)
      expect(wrapper.find('[data-test="history-count"]').text()).toBe('2 din 5 pași')
      // 200 is 53 away from 253, 52 is 201 away; 100 is a starting number, so it doesn't count.
      expect(wrapper.find('[data-test="closest"]').text()).toBe('Cel mai aproape până acum: 200')
      wrapper.unmount()
    })

    it('undo saves the steps without the last one and shows the board sent back', async () => {
      const wrapper = await mountView(jsonResponse(200, played))
      fetchMock.mockResolvedValueOnce(jsonResponse(200, { ...played, steps: [played.steps[0]] }))

      await tap(wrapper, button(wrapper, 'undo'))

      expect(fetchMock.mock.calls[1]![0]).toBe('/api/v1/games/math/today/progress/')
      expect(sentSteps(1)).toEqual([{ left: 100, op: '*', right: 2 }])
      expect(tileTexts(wrapper)).toEqual(['1', '2', '25', '50', 'NOU200'])
      expect(wrapper.findAll('[data-test="step"]')).toHaveLength(1)
      wrapper.unmount()
    })

    it('reset saves an empty list and brings back the starting numbers', async () => {
      const wrapper = await mountView(jsonResponse(200, played))
      fetchMock.mockResolvedValueOnce(jsonResponse(200, game))

      await tap(wrapper, button(wrapper, 'reset'))

      expect(sentSteps(1)).toEqual([])
      expect(tileTexts(wrapper)).toEqual(['1', '2', '2', '25', '50', '100'])
      expect(wrapper.find('[data-test="closest"]').exists()).toBe(false)
      wrapper.unmount()
    })

    it('clears a picked number when the board changes after an undo', async () => {
      const wrapper = await mountView(jsonResponse(200, played))
      fetchMock.mockResolvedValueOnce(jsonResponse(200, { ...played, steps: [played.steps[0]] }))

      await tap(wrapper, tile(wrapper, '25'))
      await tap(wrapper, button(wrapper, 'undo'))

      expect(tile(wrapper, '25').attributes('aria-pressed')).toBe('false')
      wrapper.unmount()
    })

    it('can not undo while a save is on its way', async () => {
      const wrapper = await mountView(jsonResponse(200, played))
      fetchMock.mockReturnValueOnce(new Promise(() => {}))

      await tap(wrapper, button(wrapper, 'undo'))

      expect(button(wrapper, 'undo').attributes('disabled')).toBeDefined()
      expect(button(wrapper, 'reset').attributes('disabled')).toBeDefined()
      wrapper.unmount()
    })

    it('says so when an undo can not be saved, and reloads the board', async () => {
      const wrapper = await mountView(jsonResponse(200, played))
      fetchMock.mockResolvedValueOnce(errorResponse(500, 'server_error'))
      fetchMock.mockResolvedValueOnce(jsonResponse(200, played))

      await tap(wrapper, button(wrapper, 'undo'))

      expect(wrapper.find('[data-test="refusal"]').text()).toContain('Ceva nu a mers')
      expect(fetchMock.mock.calls[2]![0]).toBe('/api/v1/games/math/today/')
      expect(wrapper.findAll('[data-test="step"]')).toHaveLength(2)
      wrapper.unmount()
    })

    it('hides undo, reset and the closest number once the game is finished, but keeps the steps', async () => {
      const wrapper = await mountView(jsonResponse(200, { ...played, status: 'completed' }))

      expect(button(wrapper, 'undo').exists()).toBe(false)
      expect(button(wrapper, 'reset').exists()).toBe(false)
      expect(wrapper.find('[data-test="closest"]').exists()).toBe(false)
      expect(wrapper.find('[data-test="closest-announce"]').text()).toBe('')
      expect(wrapper.findAll('[data-test="step"]')).toHaveLength(2)
      wrapper.unmount()
    })
  })

  describe('finish with the closest number', () => {
    const played = {
      ...game,
      steps: [{ left: 100, op: '*', right: 2, result: 200 }],
    } satisfies MathGame
    const close = {
      ...played,
      status: 'completed',
      final_result: 200,
      distance: 53,
      operations: 1,
      solved: false,
      score: 0,
      duration_ms: 42_000,
    } satisfies MathGame
    const finishButton = (wrapper: VueWrapper) => wrapper.find('[data-test="finish"]')

    it('can not finish before the first step', async () => {
      const wrapper = await mountView(jsonResponse(200, game))

      expect(finishButton(wrapper).attributes('disabled')).toBeDefined()
      wrapper.unmount()
    })

    it('sends the saved steps to submit and shows the finished game', async () => {
      const wrapper = await mountView(jsonResponse(200, played))
      fetchMock.mockResolvedValueOnce(jsonResponse(200, close))

      await tap(wrapper, finishButton(wrapper))

      const [url, init] = fetchMock.mock.calls[1]!
      expect(url).toBe('/api/v1/games/math/today/submit/')
      expect(JSON.parse(init.body)).toEqual({ steps: [{ left: 100, op: '*', right: 2 }] })
      expect(dialogText()).toContain('200 — la 53 de 253')
      expect(finishButton(wrapper).exists()).toBe(false)
      expect(
        wrapper.findAll('[data-test="tile"]').every((t) => t.attributes('disabled') !== undefined),
      ).toBe(true)
      wrapper.unmount()
    })

    it('locks the board and the buttons while finishing', async () => {
      const wrapper = await mountView(jsonResponse(200, played))
      fetchMock.mockReturnValueOnce(new Promise(() => {}))

      await tap(wrapper, finishButton(wrapper))

      for (const name of ['finish', 'undo', 'reset'])
        expect(wrapper.find(`[data-test="${name}"]`).attributes('disabled')).toBeDefined()
      expect(
        wrapper.findAll('[data-test="tile"]').every((t) => t.attributes('disabled') !== undefined),
      ).toBe(true)
      wrapper.unmount()
    })

    it('says so when the game can not be finished, and reloads the board', async () => {
      const wrapper = await mountView(jsonResponse(200, played))
      fetchMock.mockResolvedValueOnce(errorResponse(400, 'invalid_step'))
      fetchMock.mockResolvedValueOnce(jsonResponse(200, played))

      await tap(wrapper, finishButton(wrapper))

      expect(wrapper.find('[data-test="refusal"]').text()).toBe(
        'Jocul nu a putut fi terminat. Încearcă din nou.',
      )
      expect(fetchMock.mock.calls[2]![0]).toBe('/api/v1/games/math/today/')
      expect(finishButton(wrapper).attributes('disabled')).toBeUndefined()
      wrapper.unmount()
    })

    it('shows the finished game without an error when it was finished in another tab', async () => {
      const wrapper = await mountView(jsonResponse(200, played))
      fetchMock.mockResolvedValueOnce(errorResponse(409, 'already_played'))
      fetchMock.mockResolvedValueOnce(jsonResponse(200, close))

      await tap(wrapper, finishButton(wrapper))

      expect(wrapper.find('[data-test="refusal"]').exists()).toBe(false)
      expect(finishButton(wrapper).exists()).toBe(false)
      expect(dialogText()).toContain('200 — la 53 de 253')
      wrapper.unmount()
    })

    it('opens the result right away when a finished game loads, and reopens it after closing', async () => {
      const wrapper = await mountView(jsonResponse(200, close))

      expect(dialogText()).toContain('200 — la 53 de 253')
      expect(wrapper.find('[data-test="see-result"]').exists()).toBe(false)

      document.querySelector<HTMLElement>('[role="dialog"] button')!.click()
      await flushPromises()
      expect(dialogText()).toBeNull()

      await tap(wrapper, wrapper.find('[data-test="see-result"]'))
      expect(dialogText()).toContain('200 — la 53 de 253')
      wrapper.unmount()
    })

    it('opens the result again when coming back to a finished game that is still cached', async () => {
      // A new response each time: a response body can only be read once.
      fetchMock.mockImplementation(async () => jsonResponse(200, close))
      const shown = ref(true)
      const Page = defineComponent(() => () => h('div', shown.value ? [h(MathGameView)] : []))
      const wrapper = mountWithPlugins(Page)
      await settle()
      expect(dialogText()).not.toBeNull()

      shown.value = false
      await flushPromises()
      expect(dialogText()).toBeNull()

      // Same app, same cache: the game is finished from the start, so `finished` never changes.
      shown.value = true
      await settle()
      expect(dialogText()).toContain('200 — la 53 de 253')
      wrapper.unmount()
    })

    it('keeps the result closed while the game is in progress', async () => {
      const wrapper = await mountView(jsonResponse(200, played))

      expect(dialogText()).toBeNull()
      expect(wrapper.find('[data-test="see-result"]').exists()).toBe(false)
      wrapper.unmount()
    })
  })

  describe('easter eggs', () => {
    // The demo puzzle: every easter egg can be reached from these numbers.
    const demo = { ...game, target: 253, numbers: [4, 6, 7, 10, 50, 100] } satisfies MathGame
    const withSteps = (steps: MathGame['steps'], extra: Partial<MathGame> = {}) =>
      jsonResponse(200, { ...demo, steps, ...extra })
    const egg = (wrapper: VueWrapper, name: string) => wrapper.find(`[data-test="egg-${name}"]`)

    beforeEach(() => vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] }))

    async function play(wrapper: VueWrapper, left: string, op: string, right: string) {
      // By the accessible name: a computed tile also shows its "NOU" badge.
      const byValue = (value: string) =>
        wrapper
          .findAll('[data-test="tile"]')
          .find((item) => item.attributes('aria-label')?.split(',')[0] === value)!
      await tap(wrapper, byValue(left))
      await tap(wrapper, wrapper.find(`[data-test="operator-${op}"]`))
      await tap(wrapper, byValue(right))
    }

    it('juggles two hands for a 67, then hides them', async () => {
      const sixty = [{ left: 6, op: '*', right: 10, result: 60 }] as const
      const wrapper = await mountView(withSteps([...sixty]))
      fetchMock.mockResolvedValueOnce(
        withSteps([...sixty, { left: 60, op: '+', right: 7, result: 67 }]),
      )

      await play(wrapper, '60', 'add', '7')

      expect(egg(wrapper, 'hands').exists()).toBe(true)
      vi.advanceTimersByTime(EGG_MS)
      await flushPromises()
      expect(egg(wrapper, 'hands').exists()).toBe(false)
      wrapper.unmount()
    })

    it('juggles the operators for a step with a 6 and a 7', async () => {
      const wrapper = await mountView(withSteps([]))
      fetchMock.mockResolvedValueOnce(withSteps([{ left: 7, op: '-', right: 6, result: 1 }]))

      await play(wrapper, '7', 'subtract', '6')

      expect(wrapper.find('.operator-picker').classes()).toContain('operator-picker--juggling')
      wrapper.unmount()
    })

    it('glitches the board for a 404', async () => {
      const before = [
        { left: 100, op: '*', right: 4, result: 400 },
        { left: 10, op: '-', right: 6, result: 4 },
      ] as const
      const wrapper = await mountView(withSteps([...before]))
      fetchMock.mockResolvedValueOnce(
        withSteps([...before, { left: 400, op: '+', right: 4, result: 404 }]),
      )

      await play(wrapper, '400', 'add', '4')

      expect(egg(wrapper, 'glitch').text()).toBe('404 · Număr negăsit')
      expect(wrapper.find('.math-game__tiles').classes()).toContain('math-game__tiles--glitch')
      wrapper.unmount()
    })

    it('floats a π for a 314', async () => {
      const before = [
        { left: 50, op: '*', right: 6, result: 300 },
        { left: 300, op: '+', right: 10, result: 310 },
      ] as const
      const wrapper = await mountView(withSteps([...before]))
      fetchMock.mockResolvedValueOnce(
        withSteps([...before, { left: 310, op: '+', right: 4, result: 314 }]),
      )

      await play(wrapper, '310', 'add', '4')

      expect(egg(wrapper, 'pi').exists()).toBe(true)
      wrapper.unmount()
    })

    it('plays nothing for steps restored when the page loads', async () => {
      const wrapper = await mountView(withSteps([{ left: 7, op: '-', right: 6, result: 1 }]))

      expect(wrapper.find('.operator-picker').classes()).not.toContain('operator-picker--juggling')
      wrapper.unmount()
    })

    it('plays nothing for an undo, and each egg only once per game', async () => {
      const one = [{ left: 7, op: '-', right: 6, result: 1 }] as const
      const wrapper = await mountView(withSteps([]))
      const juggling = () =>
        wrapper.find('.operator-picker').classes().includes('operator-picker--juggling')

      fetchMock.mockResolvedValueOnce(withSteps([...one]))
      await play(wrapper, '7', 'subtract', '6')
      expect(juggling()).toBe(true)
      vi.advanceTimersByTime(EGG_MS)
      await flushPromises()

      fetchMock.mockResolvedValueOnce(withSteps([]))
      await tap(wrapper, wrapper.find('[data-test="undo"]'))
      expect(juggling()).toBe(false)

      fetchMock.mockResolvedValueOnce(withSteps([...one]))
      await play(wrapper, '7', 'subtract', '6')
      expect(juggling()).toBe(false)
      wrapper.unmount()
    })

    it('plays nothing when an undo leaves an easter-egg step last', async () => {
      const one = { left: 7, op: '-', right: 6, result: 1 } as const
      const two = { left: 100, op: '*', right: 4, result: 400 } as const
      const wrapper = await mountView(withSteps([one, two]))
      fetchMock.mockResolvedValueOnce(withSteps([one]))

      await tap(wrapper, wrapper.find('[data-test="undo"]'))

      expect(wrapper.find('[data-test="step"]').exists()).toBe(true)
      expect(wrapper.find('.operator-picker').classes()).not.toContain('operator-picker--juggling')
      wrapper.unmount()
    })

    it('opens the result only after the egg of the finishing step', async () => {
      const before = [
        { left: 100, op: '*', right: 4, result: 400 },
        { left: 10, op: '-', right: 6, result: 4 },
      ] as const
      const wrapper = await mountView(withSteps([...before], { target: 404 }))
      fetchMock.mockResolvedValueOnce(
        withSteps([...before, { left: 400, op: '+', right: 4, result: 404 }], {
          target: 404,
          status: 'completed',
          final_result: 404,
          distance: 0,
          solved: true,
          score: 1000,
        }),
      )

      await play(wrapper, '400', 'add', '4')
      vi.advanceTimersByTime(0)
      await flushPromises()
      expect(egg(wrapper, 'glitch').exists()).toBe(true)
      expect(dialogText()).toBeNull()

      vi.advanceTimersByTime(EGG_MS)
      await flushPromises()
      expect(egg(wrapper, 'glitch').exists()).toBe(false)
      expect(dialogText()).toContain('Ai nimerit 404!')
      wrapper.unmount()
    })
  })

  it('tells screen readers the closest number, from a region that is always there', async () => {
    const wrapper = await mountView(jsonResponse(200, game))
    const announce = () => wrapper.find('[data-test="closest-announce"]')

    expect(announce().attributes('aria-live')).toBe('polite')
    expect(announce().text()).toBe('')
    expect(wrapper.find('[data-test="closest"]').exists()).toBe(false)

    fetchMock.mockResolvedValueOnce(
      jsonResponse(200, { ...game, steps: [{ left: 100, op: '*', right: 2, result: 200 }] }),
    )
    await tap(wrapper, tile(wrapper, '100'))
    await tap(wrapper, wrapper.find('[data-test="operator-multiply"]'))
    await tap(wrapper, tile(wrapper, '2'))

    expect(announce().text()).toBe('Cel mai aproape până acum: 200')
    expect(wrapper.find('[data-test="closest"]').attributes('aria-hidden')).toBe('true')
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
