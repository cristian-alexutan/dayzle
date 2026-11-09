import { describe, expect, it } from 'vitest'

import { mountWithPlugins } from '@/tests/utils'

import Timer from './Timer.vue'

describe('Timer', () => {
  it('shows the time as m:ss', () => {
    const timer = mountWithPlugins(Timer, { props: { ms: 83_000 } })
    expect(timer.text()).toBe('1:23')
  })
})
