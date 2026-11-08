import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h } from 'vue'

import { mountWithPlugins } from '@/tests/utils'

import {
  errorCode,
  errorDetails,
  useGeoGameQuery,
  useGuessMutation,
  useRegionsQuery,
} from '../api/queries'
import type { RegionKey } from '../types'
import {
  afterFirstGuess,
  cluj,
  errorResponse,
  finishedGame,
  jsonResponse,
  newGame,
} from './fixtures'

const fetchMock = vi.fn()

function mountHooks(region?: RegionKey) {
  let hooks!: {
    game: ReturnType<typeof useGeoGameQuery>
    guess: ReturnType<typeof useGuessMutation>
  }
  mountWithPlugins(
    defineComponent({
      setup() {
        hooks = {
          game: useGeoGameQuery('today', region),
          guess: useGuessMutation('today', region),
        }
        return () => h('div')
      },
    }),
  )
  return hooks
}

async function mountLoaded(region?: RegionKey) {
  fetchMock.mockResolvedValueOnce(jsonResponse(200, newGame))
  const hooks = mountHooks(region)
  await flushPromises()
  return hooks
}

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  fetchMock.mockReset()
  vi.unstubAllGlobals()
})

describe('geo queries', () => {
  it('loads the game of the day in the default region', async () => {
    const { game } = await mountLoaded()

    expect(fetchMock.mock.calls[0]![0]).toBe('/api/v1/games/geo/today/')
    expect(game.data.value?.panorama_id).toBe('pano-1')
  })

  it('names the region in the query when one is chosen', async () => {
    const { guess } = await mountLoaded('cluj-napoca')
    fetchMock.mockResolvedValueOnce(jsonResponse(200, afterFirstGuess))

    await guess.mutateAsync({ round: 1, lat: 46.77, lng: 23.6 })

    expect(fetchMock.mock.calls[0]![0]).toBe('/api/v1/games/geo/today/?region=cluj-napoca')
    expect(fetchMock.mock.calls[1]![0]).toBe('/api/v1/games/geo/today/guess/?region=cluj-napoca')
  })

  it('sends the guess and replaces the cached game with the revealed round', async () => {
    const { game, guess } = await mountLoaded()
    fetchMock.mockResolvedValueOnce(jsonResponse(200, afterFirstGuess))

    await guess.mutateAsync({ round: 1, lat: 46.77, lng: 23.6 })

    const [url, init] = fetchMock.mock.calls[1]!
    expect(url).toBe('/api/v1/games/geo/today/guess/')
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body)).toEqual({ round: 1, lat: 46.77, lng: 23.6 })
    expect(game.data.value?.current_round).toBe(2)
    expect(game.data.value?.results[0]?.score).toBe(594)
  })

  it('shows the finished game after the fifth guess', async () => {
    const { game, guess } = await mountLoaded()
    fetchMock.mockResolvedValueOnce(jsonResponse(200, finishedGame))

    await guess.mutateAsync({ round: 5, lat: 46.77, lng: 23.6 })

    expect(game.data.value?.status).toBe('completed')
    expect(game.data.value?.total_score).toBe(2970)
  })

  it('keeps the cached game when a guess outside the region is refused', async () => {
    const { game, guess } = await mountLoaded()
    fetchMock.mockResolvedValueOnce(errorResponse(400, 'invalid', { bounds: 'outside' }))

    const error = await guess
      .mutateAsync({ round: 1, lat: 45, lng: 23 })
      .catch((caught: unknown) => caught)

    expect(errorCode(error)).toBe('invalid')
    expect(errorDetails(error)).toEqual({ bounds: 'outside' })
    expect(game.data.value).toEqual(newGame)
  })

  it('loads the regions', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(200, [cluj]))
    let regions!: ReturnType<typeof useRegionsQuery>
    mountWithPlugins(
      defineComponent({
        setup() {
          regions = useRegionsQuery()
          return () => h('div')
        },
      }),
    )
    await flushPromises()

    expect(fetchMock.mock.calls[0]![0]).toBe('/api/v1/games/geo/regions/')
    expect(regions.data.value).toEqual([cluj])
  })
})

describe('errorCode and errorDetails', () => {
  it('are null for errors that did not come from the backend', () => {
    expect(errorCode(new Error('offline'))).toBeNull()
    expect(errorDetails(new Error('offline'))).toBeNull()
  })
})
