import { afterEach, describe, expect, it, vi } from 'vitest'

import { mountWithPlugins } from '@/tests/utils'

import ConfettiBurst from '../components/ConfettiBurst.vue'

function prefersReducedMotion(reduce: boolean) {
  vi.stubGlobal(
    'matchMedia',
    vi.fn((query: string) => ({ matches: reduce && query.includes('reduce') })),
  )
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('ConfettiBurst', () => {
  it('drops confetti in the theme colors, hidden from screen readers', () => {
    prefersReducedMotion(false)

    const wrapper = mountWithPlugins(ConfettiBurst)

    const pieces = wrapper.findAll('.confetti__piece')
    expect(pieces).toHaveLength(80)
    expect(pieces[1]!.classes()).toContain('confetti__piece--accent')
    expect(wrapper.attributes('aria-hidden')).toBe('true')
  })

  it('shows nothing to players who asked for less motion', () => {
    prefersReducedMotion(true)

    const wrapper = mountWithPlugins(ConfettiBurst)

    expect(wrapper.findAll('.confetti__piece')).toHaveLength(0)
  })
})
