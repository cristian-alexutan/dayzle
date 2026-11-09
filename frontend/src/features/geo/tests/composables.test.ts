import { describe, expect, it } from 'vitest'
import { defineComponent, h, nextTick, ref } from 'vue'

import { mountWithPlugins } from '@/tests/utils'

import { useDistanceFormat } from '../composables/useDistanceFormat'
import { usePinPlacement } from '../composables/usePinPlacement'
import { isInside } from '../composables/useRegionMap'
import { cluj } from './fixtures'

describe('usePinPlacement', () => {
  function setup() {
    const round = ref(1)
    const placement = usePinPlacement({ bounds: cluj.bounds, round })
    return { round, ...placement }
  }

  it('puts the pin on a point inside the region', () => {
    const { pin, outside, place } = setup()

    place({ lat: 46.77, lng: 23.6 })

    expect(pin.value).toEqual({ lat: 46.77, lng: 23.6 })
    expect(outside.value).toBe(false)
  })

  it('refuses a point outside the region and keeps the previous pin', () => {
    const { pin, outside, place } = setup()
    place({ lat: 46.77, lng: 23.6 })

    place({ lat: 45, lng: 23.6 })

    expect(pin.value).toEqual({ lat: 46.77, lng: 23.6 })
    expect(outside.value).toBe(true)
  })

  it('clears the pin when the round changes', async () => {
    const { round, pin, place } = setup()
    place({ lat: 46.77, lng: 23.6 })

    round.value = 2
    await nextTick()

    expect(pin.value).toBeNull()
  })
})

describe('isInside', () => {
  it('counts the edges as inside', () => {
    expect(isInside(cluj.bounds, { lat: cluj.bounds.north, lng: cluj.bounds.west })).toBe(true)
    expect(isInside(cluj.bounds, { lat: cluj.bounds.north + 0.001, lng: 23.6 })).toBe(false)
  })
})

describe('useDistanceFormat', () => {
  it('shows metres under 1 km and kilometres with one decimal above', () => {
    let format!: (meters: number) => string
    mountWithPlugins(
      defineComponent({
        setup() {
          format = useDistanceFormat()
          return () => h('div')
        },
      }),
    )

    expect(format(780)).toBe('780 m')
    expect(format(1234)).toBe('1,2 km')
  })
})
