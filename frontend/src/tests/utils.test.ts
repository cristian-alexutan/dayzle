import { useQueryClient } from '@tanstack/vue-query'
import { getActivePinia } from 'pinia'
import { describe, expect, it } from 'vitest'
import { defineComponent, h } from 'vue'
import { useI18n } from 'vue-i18n'

import { mountWithPlugins } from './utils'

describe('mountWithPlugins', () => {
  it('installs i18n (Romanian by default), Pinia and TanStack Query', () => {
    const Probe = defineComponent({
      setup() {
        const { locale } = useI18n()
        const queryClient = useQueryClient()
        return () => h('p', `${locale.value}|${Boolean(queryClient)}|${Boolean(getActivePinia())}`)
      },
    })

    expect(mountWithPlugins(Probe).text()).toBe('ro|true|true')
  })
})
