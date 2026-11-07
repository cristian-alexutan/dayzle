import { flushPromises } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import { mountWithPlugins } from '@/tests/utils'

import type { SessionState } from '../types'
import AuthView from '../views/AuthView.vue'

function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const GUEST_SESSION: SessionState = {
  is_authenticated: false,
  guest_id: '11111111-1111-1111-1111-111111111111',
  user: null,
}

const USER_SESSION: SessionState = {
  is_authenticated: true,
  guest_id: '11111111-1111-1111-1111-111111111111',
  user: {
    id: 1,
    username: 'andrei',
    email: 'andrei@example.com',
    first_name: 'Andrei',
    last_name: 'Maxim',
    display_name: 'Andrei Maxim',
  },
}

afterEach(() => {
  vi.restoreAllMocks()
  localStorage.clear()
})

async function mountAuthView() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div />' } },
      { path: '/login', component: AuthView },
    ],
  })
  await router.push('/login')
  await router.isReady()

  const wrapper = mountWithPlugins(AuthView, {
    global: { plugins: [router] },
  })
  await flushPromises()
  return { wrapper, router }
}

describe('AuthView', () => {
  it('renders guest state and lets the visitor continue as a guest back to home', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve(jsonResponse(200, GUEST_SESSION))),
    )

    const { wrapper, router } = await mountAuthView()

    expect(wrapper.find('[data-test="guest-panel"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="guest-badge"]').text()).toContain('Joci ca vizitator')
    expect(wrapper.find('[data-test="login-back-home"]').text()).toContain('Continuă ca vizitator')

    await wrapper.find('[data-test="login-back-home"]').trigger('click')
    await flushPromises()

    expect(router.currentRoute.value.path).toBe('/')
    wrapper.unmount()
  })

  it('renders signed-in user profile and logs out back to guest state', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(200, USER_SESSION))
      .mockResolvedValueOnce(jsonResponse(200, GUEST_SESSION))
    vi.stubGlobal('fetch', fetchMock)

    const { wrapper } = await mountAuthView()

    expect(wrapper.find('[data-test="signed-in-panel"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="user-display-name"]').text()).toBe('Andrei Maxim')
    expect(wrapper.find('[data-test="user-email"]').text()).toBe('andrei@example.com')

    await wrapper.find('[data-test="logout-button"]').trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-test="guest-panel"]').exists()).toBe(true)
    wrapper.unmount()
  })
})
