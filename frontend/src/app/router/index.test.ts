import { flushPromises } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import App from '@/app/App.vue'
import { mountWithPlugins } from '@/tests/utils'

import { appRoutes } from './index'

vi.stubGlobal('matchMedia', () => ({ matches: false, addEventListener: vi.fn() }))

afterEach(() => localStorage.clear())

describe('app router and layout', () => {
  it('defines routes for home, login, and all five games', () => {
    const paths = appRoutes.map((route) => route.path)
    expect(paths).toEqual([
      '/',
      '/login',
      '/games/word',
      '/games/math',
      '/games/logic',
      '/games/trivia',
      '/games/geo',
    ])
  })

  it('renders the header and navigates between home, login, and game placeholders using appRoutes', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: appRoutes,
    })
    await router.push('/')
    await router.isReady()

    const wrapper = mountWithPlugins(App, {
      global: { plugins: [router] },
    })

    expect(wrapper.find('[data-test="home-page"]').exists()).toBe(true)

    await router.push('/login')
    await flushPromises()
    expect(wrapper.find('[data-test="login-card"]').exists()).toBe(true)

    await wrapper.find('[data-test="login-back-home"]').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/')

    await router.push('/games/trivia')
    await flushPromises()
    expect(wrapper.find('[data-test="game-coming-soon"]').exists()).toBe(true)
  })
})
