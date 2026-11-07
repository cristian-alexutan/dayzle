import { flushPromises } from '@vue/test-utils'
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

    expect(wrapper.find('h1').text()).toBe('Atinge ținta')
    expect(wrapper.find('[data-test="target"]').text()).toBe('Ținta: 253')
    const numbers = wrapper.findAll('[data-test="numbers"] li').map((item) => item.text())
    expect(numbers).toEqual(['1', '2', '2', '25', '50', '100'])
    wrapper.unmount()
  })

  it('says when there is no puzzle today', async () => {
    const wrapper = await mountView(errorResponse(404, 'no_puzzle'))

    expect(wrapper.find('[data-test="no-puzzle"]').text()).toContain('Revino mâine')
    expect(wrapper.find('button').exists()).toBe(false)
    wrapper.unmount()
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
