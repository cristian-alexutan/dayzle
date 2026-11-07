import { flushPromises } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import App from '@/app/App.vue'
import GamePlaceholderView from '@/app/views/GamePlaceholderView.vue'
import HomeView from '@/app/views/HomeView.vue'
import { authRoutes } from '@/features/auth'
import { mountWithPlugins } from '@/tests/utils'

import { appRoutes } from './index'

vi.stubGlobal('matchMedia', () => ({ matches: false, addEventListener: vi.fn() }))

function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const GUEST_SESSION = {
  is_authenticated: false,
  guest_id: '11111111-1111-1111-1111-111111111111',
  user: null,
}

afterEach(() => {
  vi.restoreAllMocks()
  localStorage.clear()
})

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

  it('renders the header and navigates between home, login, and game placeholders', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve(jsonResponse(200, GUEST_SESSION))),
    )

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', name: 'home', component: HomeView },
        ...authRoutes,
        { path: '/games/word', name: 'word', component: { template: '<div />' } },
        { path: '/games/logic', name: 'logic', component: { template: '<div />' } },
        { path: '/games/math', name: 'math', component: { template: '<div />' } },
        { path: '/games/trivia', name: 'trivia', component: { template: '<div />' } },
        {
          path: '/games/geo',
          name: 'geo',
          component: GamePlaceholderView,
          props: { gameKey: 'geo' },
        },
      ],
    })
    await router.push('/')
    await router.isReady()

    const wrapper = mountWithPlugins(App, {
      global: { plugins: [router] },
    })
    await flushPromises()

    expect(wrapper.find('[data-test="home-page"]').exists()).toBe(true)

    await router.push('/login')
    await flushPromises()
    expect(wrapper.find('[data-test="login-card"]').exists()).toBe(true)

    await wrapper.find('[data-test="login-back-home"]').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/')

    await router.push('/games/geo')
    await flushPromises()
    expect(wrapper.find('[data-test="game-coming-soon"]').exists()).toBe(true)
  })
})
