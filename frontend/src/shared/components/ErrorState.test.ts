import { describe, expect, it } from 'vitest'

import { mountWithPlugins } from '@/tests/utils'

import ErrorState from './ErrorState.vue'

describe('ErrorState', () => {
  it('shows the message without a retry button by default', () => {
    const wrapper = mountWithPlugins(ErrorState, { props: { message: 'Eroare' } })

    expect(wrapper.text()).toContain('Eroare')
    expect(wrapper.find('button').exists()).toBe(false)
  })

  it('emits retry when it can be retried', async () => {
    const wrapper = mountWithPlugins(ErrorState, { props: { message: 'Eroare', retryable: true } })

    await wrapper.find('button').trigger('click')

    expect(wrapper.emitted('retry')).toHaveLength(1)
  })
})
