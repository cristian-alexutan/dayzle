import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory } from 'vue-router'

import App from '@/app/App.vue'
import type { SessionState } from '@/features/auth'
import { mountWithPlugins } from '@/tests/utils'

import { appRoutes, createAppRouter } from './index'

const fetchSessionMock = vi.fn<() => Promise<SessionState>>()

vi.mock('@/features/auth/api/endpoints', () => ({
  fetchSession: () => fetchSessionMock(),
  loginWithGoogle: vi.fn(),
  logoutSession: vi.fn(),
}))

vi.stubGlobal('matchMedia', () => ({ matches: false, addEventListener: vi.fn() }))

const guestSession: SessionState = {
  is_authenticated: false,
  guest_id: '00000000-0000-0000-0000-000000000001',
  user: null,
}

const signedInSession: SessionState = {
  is_authenticated: true,
  guest_id: '00000000-0000-0000-0000-000000000001',
  user: {
    id: 1,
    username: 'andrei',
    email: 'andrei@example.com',
    first_name: 'Andrei',
    last_name: 'Maxim',
    display_name: 'Andrei Maxim',
  },
}

beforeEach(() => {
  fetchSessionMock.mockResolvedValue(guestSession)
})

afterEach(() => {
  localStorage.clear()
  vi.clearAllMocks()
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

  it('renders the header and navigates between home, login, and a game', async () => {
    const router = createAppRouter(createMemoryHistory(), () => guestSession)
    await router.push('/')
    await router.isReady()

    const wrapper = mountWithPlugins(App, {
      global: { plugins: [router] },
    })

    expect(wrapper.find('[data-test="home-page"]').exists()).toBe(true)

    await router.push('/login')
    await flushPromises()
    expect(wrapper.find('[data-test="guest-panel"]').exists()).toBe(true)

    await wrapper.find('[data-test="login-back-home"]').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/')

    // The game's first request never settles here: only the page itself is checked.
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockReturnValue(new Promise(() => {}))
    await router.push('/games/trivia')
    await flushPromises()
    expect(wrapper.find('[data-test="trivia-game"]').exists()).toBe(true)
    fetchSpy.mockRestore()
  })

  it('enforces guest-only and auth-required route guards in the router', async () => {
    let currentSession: SessionState | undefined = guestSession
    const router = createAppRouter(createMemoryHistory(), () => currentSession, [
      {
        path: '/account',
        name: 'account',
        component: { template: '<div data-test="account-page" />' },
        meta: { requiresAuth: true },
      },
    ])

    await router.push('/account')
    await router.isReady()
    expect(router.currentRoute.value.path).toBe('/login')
    expect(router.currentRoute.value.query).toEqual({ next: '/account' })

    currentSession = signedInSession
    await router.push('/login')
    expect(router.currentRoute.value.path).toBe('/')

    await router.push('/account')
    expect(router.currentRoute.value.path).toBe('/account')
  })
})
