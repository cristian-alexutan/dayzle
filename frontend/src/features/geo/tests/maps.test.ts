import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { mountWithPlugins } from '@/tests/utils'

import GeoMap from '../components/GeoMap.vue'
import RevealMap from '../components/RevealMap.vue'
import StreetViewPanorama from '../components/StreetViewPanorama.vue'
import { finishedGame, cluj, afterFirstGuess } from './fixtures'
import {
  fake,
  installFakeGoogleMaps,
  shapesOnMap,
  uninstallFakeGoogleMaps,
  type FakeShape,
} from './fakeGoogleMaps'

beforeEach(installFakeGoogleMaps)
afterEach(uninstallFakeGoogleMaps)

describe('StreetViewPanorama', () => {
  it('shows the round without the address or street names', async () => {
    const wrapper = mountWithPlugins(StreetViewPanorama, { props: { panoramaId: 'pano-1' } })
    await flushPromises()

    const panorama = fake.panoramas[0]!
    expect(panorama.options).toMatchObject({
      pano: 'pano-1',
      addressControl: false,
      showRoadLabels: false,
    })
    expect(wrapper.find('[data-test="maps-unavailable"]').exists()).toBe(false)
    wrapper.unmount()
  })

  it('moves to the next panorama facing north', async () => {
    const wrapper = mountWithPlugins(StreetViewPanorama, { props: { panoramaId: 'pano-1' } })
    await flushPromises()

    await wrapper.setProps({ panoramaId: 'pano-2' })

    const panorama = fake.panoramas[0]!
    expect(panorama.setPano).toHaveBeenCalledWith('pano-2')
    expect(panorama.setPov).toHaveBeenCalledWith({ heading: 0, pitch: 0 })
    wrapper.unmount()
  })

  it('says so when no browser key is configured', async () => {
    vi.stubEnv('VITE_GOOGLE_MAPS_BROWSER_KEY', '')
    vi.spyOn(console, 'warn').mockImplementation(() => {})

    const wrapper = mountWithPlugins(StreetViewPanorama, { props: { panoramaId: 'pano-1' } })
    await flushPromises()

    expect(wrapper.find('[data-test="maps-unavailable"]').text()).toBe(
      'Harta nu poate fi afișată acum.',
    )
    expect(fake.panoramas).toHaveLength(0)
    wrapper.unmount()
  })

  it('says so when Google cannot be loaded', async () => {
    fake.importLibrary.mockRejectedValueOnce(new Error('offline'))

    const wrapper = mountWithPlugins(StreetViewPanorama, { props: { panoramaId: 'pano-1' } })
    await flushPromises()

    expect(wrapper.find('[data-test="maps-unavailable"]').exists()).toBe(true)
    wrapper.unmount()
  })
})

describe('GeoMap', () => {
  async function mountMap(props: Partial<InstanceType<typeof GeoMap>['$props']> = {}) {
    const wrapper = mountWithPlugins(GeoMap, {
      props: { bounds: cluj.bounds, pin: null, ...props },
    })
    await flushPromises()
    return wrapper
  }

  it('shows the whole region, without the Street View pegman', async () => {
    const wrapper = await mountMap()

    const map = fake.maps[0]!
    expect(map.options).toMatchObject({ streetViewControl: false, clickableIcons: false })
    expect(map.fitBounds).toHaveBeenCalledWith(cluj.bounds, 0)
    expect(shapesOnMap('rectangle')[0]!.options.bounds).toEqual(cluj.bounds)
    wrapper.unmount()
  })

  it('places the pin where the player clicks', async () => {
    const wrapper = await mountMap()

    fake.maps[0]!.click({ lat: 46.77, lng: 23.6 })

    expect(wrapper.emitted('place')).toEqual([[{ lat: 46.77, lng: 23.6 }]])
    wrapper.unmount()
  })

  it('ignores clicks while a guess is being sent', async () => {
    const wrapper = await mountMap({ disabled: true })

    fake.maps[0]!.click({ lat: 46.77, lng: 23.6 })

    expect(wrapper.emitted('place')).toBeUndefined()
    wrapper.unmount()
  })

  it('draws, moves and removes the pin', async () => {
    const wrapper = await mountMap()

    await wrapper.setProps({ pin: { lat: 46.77, lng: 23.6 } })
    expect(shapesOnMap('marker').map((marker) => marker.options.position)).toEqual([
      { lat: 46.77, lng: 23.6 },
    ])

    await wrapper.setProps({ pin: { lat: 46.78, lng: 23.61 } })
    expect(shapesOnMap('marker').map((marker) => marker.options.position)).toEqual([
      { lat: 46.78, lng: 23.61 },
    ])

    await wrapper.setProps({ pin: null })
    expect(shapesOnMap('marker')).toHaveLength(0)
    wrapper.unmount()
  })
})

describe('RevealMap', () => {
  const positions = (shapes: FakeShape[]) => shapes.map((shape) => shape.options.position)

  it('shows the guess, the real spot and a line between, zoomed to them', async () => {
    const result = afterFirstGuess.results[0]!
    const wrapper = mountWithPlugins(RevealMap, {
      props: { bounds: cluj.bounds, results: [result] },
    })
    await flushPromises()

    expect(positions(shapesOnMap('marker'))).toEqual([result.guess, result.location])
    expect(shapesOnMap('polyline')[0]!.options.path).toEqual([result.guess, result.location])
    const map = fake.maps[0]!
    expect(map.fitBounds).toHaveBeenLastCalledWith(
      expect.objectContaining({ points: [result.guess, result.location] }),
      48,
    )
    wrapper.unmount()
  })

  it('does not zoom closer than street level for a very close guess', async () => {
    const wrapper = mountWithPlugins(RevealMap, {
      props: { bounds: cluj.bounds, results: afterFirstGuess.results },
    })
    await flushPromises()
    const map = fake.maps[0]!
    map.zoom = 20

    map.trigger('idle')

    expect(map.setZoom).toHaveBeenCalledWith(16)
    wrapper.unmount()
  })

  it('numbers the real spots on the end map', async () => {
    const wrapper = mountWithPlugins(RevealMap, {
      props: { bounds: cluj.bounds, results: finishedGame.results, numbered: true },
    })
    await flushPromises()

    const labels = shapesOnMap('marker')
      .map((marker) => (marker.options.label as { text: string } | undefined)?.text)
      .filter(Boolean)
    expect(labels).toEqual(['1', '2', '3', '4', '5'])
    expect(shapesOnMap('polyline')).toHaveLength(5)
    wrapper.unmount()
  })
})
