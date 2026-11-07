import { flushPromises } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import { useThemeStore } from '@/shared/stores/theme'
import { mountWithPlugins } from '@/tests/utils'

import AppHeader from './AppHeader.vue'

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

const USER_SESSION = {
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

function mountHeader() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div />' } },
      { path: '/login', component: { template: '<div />' } },
    ],
  })
  return {
    router,
    wrapper: mountWithPlugins(AppHeader, {
      global: { plugins: [router] },
    }),
  }
}

describe('AppHeader', () => {
  it('renders the brand logo, home link and login button for guests', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve(jsonResponse(200, GUEST_SESSION))),
    )
    const { wrapper, router } = mountHeader()
    await router.isReady()
    await flushPromises()

    expect(wrapper.find('[data-test="brand-link"]').text()).toContain('Dayzle')
    expect(wrapper.find('[data-test="home-link"]').text()).toContain('Acasă')
    expect(wrapper.find('[data-test="login-link"]').text()).toContain('Autentificare')
  })

  it('shows the signed-in user name and logs out when clicking the logout button', async () => {
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(() => Promise.resolve(jsonResponse(200, USER_SESSION)))
      .mockImplementationOnce(() => Promise.resolve(jsonResponse(200, GUEST_SESSION)))
    vi.stubGlobal('fetch', fetchMock)

    const { wrapper, router } = mountHeader()
    await router.isReady()
    await flushPromises()

    expect(wrapper.find('[data-test="user-chip"]').text()).toContain('Andrei Maxim')
    expect(wrapper.find('[data-test="logout-link"]').text()).toContain('Deconectare')

    await wrapper.find('[data-test="logout-link"]').trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-test="login-link"]').exists()).toBe(true)
  })

  it('navigates to /login when clicking the login button', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve(jsonResponse(200, GUEST_SESSION))),
    )
    const { wrapper, router } = mountHeader()
    await router.isReady()
    await flushPromises()

    await wrapper.find('[data-test="login-link"]').trigger('click')
    await flushPromises()

    expect(router.currentRoute.value.path).toBe('/login')
  })

  it('cycles the theme from its button', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve(jsonResponse(200, GUEST_SESSION))),
    )
    const { wrapper, router } = mountHeader()
    await router.isReady()
    const theme = useThemeStore()
    expect(theme.mode).toBe('auto')

    await wrapper.find('[data-test="theme"]').trigger('click')

    expect(theme.mode).toBe('light')
  })

  it('switches the language and remembers it', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve(jsonResponse(200, GUEST_SESSION))),
    )
    const { wrapper, router } = mountHeader()
    await router.isReady()
    await flushPromises()
    const language = wrapper.find('[data-test="language"]')
    expect(language.text()).toBe('RO')

    await language.trigger('click')

    expect(language.text()).toBe('EN')
    expect(document.documentElement.lang).toBe('en')
    expect(localStorage.getItem('dayzle.locale')).toBe('en')
    expect(wrapper.find('[data-test="home-link"]').text()).toContain('Home')
    expect(wrapper.find('[data-test="login-link"]').text()).toContain('Sign in')
  })
})
