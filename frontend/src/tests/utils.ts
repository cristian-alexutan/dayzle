import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'
import { mount, type ComponentMountingOptions } from '@vue/test-utils'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import type { Component } from 'vue'

import { createAppI18n } from '@/app/i18n'
import { DayzlePreset } from '@/app/theme/preset'

/** Mount a component with the same plugins as the app (i18n, Pinia, TanStack Query, PrimeVue). */
export function mountWithPlugins<C extends Component>(
  component: C,
  options: ComponentMountingOptions<C> = {},
) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return mount(component, {
    ...options,
    global: {
      ...options.global,
      plugins: [
        createAppI18n(),
        createPinia(),
        [VueQueryPlugin, { queryClient }],
        [PrimeVue, { theme: { preset: DayzlePreset } }],
        ...(options.global?.plugins ?? []),
      ],
    },
  } as ComponentMountingOptions<C>)
}
