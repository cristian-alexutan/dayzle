import { flushPromises, type VueWrapper } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { mountWithPlugins } from '@/tests/utils'

import ConfettiBurst from '../components/ConfettiBurst.vue'
import GeoMap from '../components/GeoMap.vue'
import GeoResult from '../components/GeoResult.vue'
import RevealMap from '../components/RevealMap.vue'
import StreetViewPanorama from '../components/StreetViewPanorama.vue'
import type { GeoGame } from '../types'
import GeoGameView from '../views/GeoGameView.vue'
import {
  afterFirstGuess,
  cluj,
  errorResponse,
  finishedGame,
  jsonResponse,
  newGame,
} from './fixtures'

const fetchMock = vi.fn()

/** Google's panorama and maps are replaced by stubs; maps.test.ts covers them. */
const stubs = { GeoMap: true, RevealMap: true, StreetViewPanorama: true }

const inside = { lat: 46.77, lng: 23.6 }

async function mountView(firstResponse: Response) {
  fetchMock.mockResolvedValueOnce(firstResponse)
  const wrapper = mountWithPlugins(GeoGameView, { global: { stubs } })
  await flushPromises()
  return wrapper
}

async function click(wrapper: VueWrapper, selector: string) {
  await wrapper.find(selector).trigger('click')
  await flushPromises()
}

/** Open the map if the panorama is showing, as a player would. */
async function openMap(wrapper: VueWrapper) {
  if (wrapper.find('[data-test="open-map"]').exists())
    await click(wrapper, '[data-test="open-map"]')
}

async function placePin(wrapper: VueWrapper, point = inside) {
  await openMap(wrapper)
  wrapper.findComponent(GeoMap).vm.$emit('place', point)
  await flushPromises()
}

const isHidden = (wrapper: VueWrapper, component: typeof GeoMap | typeof StreetViewPanorama) =>
  wrapper.findComponent(component).classes().includes('geo-game__layer--hidden')

/** Place a pin and guess, with the server answering `response`. */
async function guess(wrapper: VueWrapper, response: Response) {
  await placePin(wrapper)
  fetchMock.mockResolvedValueOnce(response)
  await click(wrapper, '[data-test="guess"]')
}

/** The game after `rounds` guesses, each worth 594 points. */
function gameAfter(rounds: number): GeoGame {
  if (rounds === 5) return finishedGame
  return {
    ...newGame,
    current_round: rounds + 1,
    panorama_id: `pano-${rounds + 1}`,
    results: finishedGame.results.slice(0, rounds),
    total_score: 594 * rounds,
  }
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

    const wrapper = mountWithPlugins(GeoGameView, { global: { stubs } })

    expect(wrapper.find('[aria-label="Se încarcă jocul"]').exists()).toBe(true)
    wrapper.unmount()
  })

  it('draws the title with a globe for the "o", read out as GeoGuesser', async () => {
    const wrapper = await mountView(jsonResponse(200, afterFirstGuess))

    const title = wrapper.find('h1 [data-test="title"]')
    expect(title.find('.geo-title__label').text()).toBe('GeoGuesser')
    const visible = title.find('[aria-hidden="true"]')
    expect(visible.text().replace(/\s+/g, '')).toBe('GeGuesser')
    expect(visible.find('i.pi-globe').exists()).toBe(true)
    wrapper.unmount()
  })

  it('shows the round and the score so far, without a subtitle', async () => {
    const wrapper = await mountView(jsonResponse(200, afterFirstGuess))

    expect(wrapper.find('[data-test="subtitle"]').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('Cluj-Napoca ·')
    expect(wrapper.find('[data-test="round"]').text()).toBe('Runda 2 din 5')
    expect(wrapper.find('[data-test="score"]').text()).toBe('594 / 5000 puncte')
    expect(wrapper.findComponent(StreetViewPanorama).props('panoramaId')).toBe('pano-2')
    wrapper.unmount()
  })

  it('starts on the panorama, with the map made only when opened', async () => {
    const wrapper = await mountView(jsonResponse(200, newGame))

    expect(isHidden(wrapper, StreetViewPanorama)).toBe(false)
    expect(wrapper.findComponent(GeoMap).exists()).toBe(false)
    expect(wrapper.find('[data-test="guess"]').exists()).toBe(false)

    await click(wrapper, '[data-test="open-map"]')

    expect(isHidden(wrapper, GeoMap)).toBe(false)
    expect(isHidden(wrapper, StreetViewPanorama)).toBe(true)
    expect(wrapper.find('[data-test="guess"]').attributes('disabled')).toBeDefined()
    wrapper.unmount()
  })

  it('lets the player guess only once a pin is placed', async () => {
    const wrapper = await mountView(jsonResponse(200, newGame))

    await placePin(wrapper)

    expect(wrapper.findComponent(GeoMap).props('pin')).toEqual(inside)
    expect(wrapper.find('[data-test="guess"]').attributes('disabled')).toBeUndefined()
    wrapper.unmount()
  })

  it('goes back and forth between the panorama and the map, keeping both', async () => {
    const wrapper = await mountView(jsonResponse(200, newGame))
    await placePin(wrapper)

    await click(wrapper, '[data-test="back-to-panorama"]')
    expect(isHidden(wrapper, StreetViewPanorama)).toBe(false)
    expect(isHidden(wrapper, GeoMap)).toBe(true)

    await click(wrapper, '[data-test="open-map"]')
    expect(isHidden(wrapper, GeoMap)).toBe(false)
    expect(wrapper.findComponent(GeoMap).props('pin')).toEqual(inside)
    expect(wrapper.findAllComponents(StreetViewPanorama)).toHaveLength(1)
    wrapper.unmount()
  })

  it('refuses a pin outside the region without asking the server', async () => {
    const wrapper = await mountView(jsonResponse(200, newGame))

    await placePin(wrapper, { lat: 45, lng: 23.6 })

    expect(wrapper.find('[data-test="guess-error"]').text()).toBe('Alege un punct din Cluj-Napoca.')
    expect(wrapper.findComponent(GeoMap).props('pin')).toBeNull()
    expect(fetchMock).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })

  it('sends the guess, then reveals the real spot with the distance and points', async () => {
    const wrapper = await mountView(jsonResponse(200, newGame))

    await guess(wrapper, jsonResponse(200, afterFirstGuess))

    const [url, init] = fetchMock.mock.calls[1]!
    expect(url).toBe('/api/v1/games/geo/today/guess/')
    expect(JSON.parse(init.body)).toEqual({ round: 1, ...inside })
    expect(wrapper.find('[data-test="round"]').text()).toBe('Runda 1 din 5')
    const reveal = wrapper.find('[data-test="reveal"]')
    expect(reveal.find('strong').text()).toBe('594 puncte')
    expect(reveal.find('span').text()).toBe('la 780 m de locul real')
    expect(wrapper.findComponent(RevealMap).props('results')).toEqual(afterFirstGuess.results)
    expect(wrapper.findComponent(StreetViewPanorama).exists()).toBe(false)
    expect(wrapper.findComponent(ConfettiBurst).exists()).toBe(false)
    wrapper.unmount()
  })

  it('celebrates a guess under 100 m with confetti, until the next round', async () => {
    const wrapper = await mountView(jsonResponse(200, newGame))
    const [round] = afterFirstGuess.results
    const close = { ...afterFirstGuess, results: [{ ...round!, distance_m: 99, score: 1000 }] }

    await guess(wrapper, jsonResponse(200, close))
    expect(wrapper.findComponent(ConfettiBurst).exists()).toBe(true)

    await click(wrapper, '[data-test="next"]')
    expect(wrapper.findComponent(ConfettiBurst).exists()).toBe(false)
    wrapper.unmount()
  })

  it('gives no confetti for a guess exactly 100 m away', async () => {
    const wrapper = await mountView(jsonResponse(200, newGame))
    const [round] = afterFirstGuess.results
    const edge = { ...afterFirstGuess, results: [{ ...round!, distance_m: 100 }] }

    await guess(wrapper, jsonResponse(200, edge))

    expect(wrapper.findComponent(ConfettiBurst).exists()).toBe(false)
    wrapper.unmount()
  })

  it('moves on to the next round on its panorama, with no pin', async () => {
    const wrapper = await mountView(jsonResponse(200, newGame))
    await guess(wrapper, jsonResponse(200, afterFirstGuess))

    await click(wrapper, '[data-test="next"]')

    expect(wrapper.find('[data-test="round"]').text()).toBe('Runda 2 din 5')
    expect(wrapper.findComponent(StreetViewPanorama).props('panoramaId')).toBe('pano-2')
    expect(isHidden(wrapper, StreetViewPanorama)).toBe(false)
    expect(wrapper.findComponent(GeoMap).exists()).toBe(false)

    await openMap(wrapper)
    expect(wrapper.findComponent(GeoMap).props('pin')).toBeNull()
    wrapper.unmount()
  })

  it('shows the end screen after the fifth round is revealed', async () => {
    const wrapper = await mountView(jsonResponse(200, gameAfter(4)))

    await guess(wrapper, jsonResponse(200, finishedGame))
    expect(wrapper.find('[data-test="next"]').text()).toBe('Vezi rezultatul')
    await click(wrapper, '[data-test="next"]')

    const result = wrapper.findComponent(GeoResult)
    expect(result.find('h2').text()).toBe('Bravo!')
    expect(result.text()).toContain('2970/5000')
    expect(result.findAll('[data-test="result-round"]')).toHaveLength(5)
    expect(result.findComponent(RevealMap).props('numbered')).toBe(true)
    wrapper.unmount()
  })

  it('shows the end screen right away for a game finished earlier', async () => {
    const wrapper = await mountView(jsonResponse(200, finishedGame))

    expect(wrapper.find('[data-test="round"]').exists()).toBe(false)
    expect(wrapper.findComponent(GeoResult).text()).toContain('Runda 1')
    expect(wrapper.findComponent(GeoResult).text()).toContain('1:35')
    wrapper.unmount()
  })

  it('keeps the pin and explains when the server refuses a point outside the region', async () => {
    const wrapper = await mountView(jsonResponse(200, newGame))

    await guess(wrapper, errorResponse(400, 'invalid', { bounds: 'outside' }))

    expect(wrapper.find('[data-test="guess-error"]').text()).toBe('Alege un punct din Cluj-Napoca.')
    expect(wrapper.find('[data-test="round"]').text()).toBe('Runda 1 din 5')
    wrapper.unmount()
  })

  it('reloads the game when the round was already guessed elsewhere', async () => {
    const wrapper = await mountView(jsonResponse(200, newGame))
    fetchMock.mockResolvedValueOnce(errorResponse(409, 'already_answered'))
    fetchMock.mockResolvedValueOnce(jsonResponse(200, afterFirstGuess))

    await placePin(wrapper)
    await click(wrapper, '[data-test="guess"]')

    expect(fetchMock.mock.calls[2]![0]).toBe('/api/v1/games/geo/today/')
    expect(wrapper.find('[data-test="guess-error"]').text()).toBe(
      'Jocul s-a schimbat între timp, așa că l-am reîncărcat.',
    )
    expect(wrapper.find('[data-test="round"]').text()).toBe('Runda 2 din 5')
    wrapper.unmount()
  })

  it('keeps the pin to try again when the server cannot be reached', async () => {
    const wrapper = await mountView(jsonResponse(200, newGame))

    await guess(wrapper, errorResponse(500, 'server_error'))

    expect(wrapper.find('[data-test="guess-error"]').text()).toBe(
      'Ceva nu a mers. Încearcă din nou.',
    )
    expect(wrapper.findComponent(GeoMap).props('pin')).toEqual(inside)
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

  it('names the region today was started in and continues the game there', async () => {
    fetchMock.mockResolvedValueOnce(errorResponse(409, 'region_locked', { region: 'cluj-napoca' }))
    fetchMock.mockResolvedValueOnce(jsonResponse(200, [cluj]))
    const wrapper = mountWithPlugins(GeoGameView, { global: { stubs } })
    await flushPromises()

    const locked = wrapper.find('[data-test="region-locked"]')
    expect(locked.text()).toContain('Ai început deja jocul de azi în Cluj-Napoca.')
    expect(fetchMock.mock.calls[1]![0]).toBe('/api/v1/games/geo/regions/')

    fetchMock.mockResolvedValueOnce(jsonResponse(200, afterFirstGuess))
    await click(wrapper, '[data-test="continue-region"]')

    expect(fetchMock.mock.calls[2]![0]).toBe('/api/v1/games/geo/today/?region=cluj-napoca')
    expect(wrapper.find('[data-test="round"]').text()).toBe('Runda 2 din 5')

    fetchMock.mockResolvedValueOnce(jsonResponse(200, gameAfter(2)))
    await placePin(wrapper)
    await click(wrapper, '[data-test="guess"]')
    expect(fetchMock.mock.calls[3]![0]).toBe('/api/v1/games/geo/today/guess/?region=cluj-napoca')
    wrapper.unmount()
  })

  it('shows the region key until the regions have loaded', async () => {
    fetchMock.mockResolvedValueOnce(errorResponse(409, 'region_locked', { region: 'cluj-napoca' }))
    fetchMock.mockReturnValueOnce(new Promise(() => {}))
    const wrapper = mountWithPlugins(GeoGameView, { global: { stubs } })
    await flushPromises()

    expect(wrapper.find('[data-test="continue-region"]').text()).toBe('Continuă în cluj-napoca')
    wrapper.unmount()
  })

  it('offers a retry after any other error', async () => {
    const wrapper = await mountView(errorResponse(500, 'server_error'))
    fetchMock.mockResolvedValueOnce(jsonResponse(200, afterFirstGuess))

    await click(wrapper, 'button')

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
