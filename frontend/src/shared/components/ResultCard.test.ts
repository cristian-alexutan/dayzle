import { describe, expect, it } from 'vitest'

import { mountWithPlugins } from '@/tests/utils'

import ResultCard from './ResultCard.vue'

describe('ResultCard', () => {
  it('shows the result, details and time', () => {
    const wrapper = mountWithPlugins(ResultCard, {
      props: { result: '3/6', durationMs: 65_000 },
      slots: { default: 'carte' },
    })

    expect(wrapper.text()).toContain('3/6')
    expect(wrapper.text()).toContain('carte')
    expect(wrapper.text()).toContain('1:05')
  })
})
