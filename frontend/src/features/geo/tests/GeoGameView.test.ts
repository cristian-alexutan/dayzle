import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { mountWithPlugins } from '@/tests/utils'

import GeoGameView from '../views/GeoGameView.vue'
import { afterFirstGuess, errorResponse, finishedGame, jsonResponse } from './fixtures'

const fetchMock = vi.fn()

async function mountView(firstResponse: Response) {
  fetchMock.mockResolvedValueOnce(firstResponse)
  const wrapper = mountWithPlugins(GeoGameView)
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

describe('GeoGameView', () => {
  it('shows a spinner while the game loads', () => {
    fetchMock.mockReturnValueOnce(new Promise(() => {}))

    const wrapper = mountWithPlugins(GeoGameView)

    expect(wrapper.find('[aria-label="Se încarcă jocul"]').exists()).toBe(true)
    wrapper.unmount()
  })

  it('shows the region, the day, the round and the score so far', async () => {
    const wrapper = await mountView(jsonResponse(200, afterFirstGuess))

    expect(wrapper.find('h1').text()).toBe('GeoGuesser')
    expect(wrapper.find('[data-test="subtitle"]').text()).toBe(
      'Cluj-Napoca · duminică, 8 noiembrie',
    )
    expect(wrapper.find('[data-test="round"]').text()).toBe('Runda 2 din 5')
    expect(wrapper.find('[data-test="score"]').text()).toBe('594 / 5000 puncte')
    wrapper.unmount()
  })

  it('shows the final score of a finished game', async () => {
    const wrapper = await mountView(jsonResponse(200, finishedGame))

    expect(wrapper.find('[data-test="round"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="finished"]').text()).toBe('Ai terminat! Scor: 2970 din 5000')
    wrapper.unmount()
  })

  it('says when there is no game today', async () => {
    const wrapper = await mountView(errorResponse(404, 'no_puzzle'))

    expect(wrapper.find('[data-test="no-puzzle"]').exists()).toBe(true)
    wrapper.unmount()
  })

  it('treats an unknown region as a setup problem, not a day without a game', async () => {
    const wrapper = await mountView(errorResponse(404, 'no_region'))

    expect(wrapper.find('[data-test="no-puzzle"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('GeoGuesser nu este disponibil acum.')
    expect(wrapper.find('button').exists()).toBe(false)
    wrapper.unmount()
  })

  it('names the region today was started in when another one is locked', async () => {
    const wrapper = await mountView(errorResponse(409, 'region_locked', { region: 'cluj-napoca' }))

    expect(wrapper.find('[data-test="region-locked"]').text()).toContain('cluj-napoca')
    wrapper.unmount()
  })

  it('offers a retry after any other error', async () => {
    const wrapper = await mountView(errorResponse(500, 'server_error'))
    fetchMock.mockResolvedValueOnce(jsonResponse(200, afterFirstGuess))

    await wrapper.find('button').trigger('click')
    await flushPromises()

    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(wrapper.find('[data-test="round"]').exists()).toBe(true)
    wrapper.unmount()
  })

  it('sends a heartbeat every 15 s while the game is in progress', async () => {
    vi.useFakeTimers()
    const wrapper = await mountView(jsonResponse(200, afterFirstGuess))
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }))

    await vi.advanceTimersByTimeAsync(15_000)

    expect(fetchMock.mock.calls[1]![0]).toBe('/api/v1/results/geo/today/heartbeat/')
    wrapper.unmount()
  })
})
