import { flushPromises } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import { useThemeStore } from '@/shared/stores/theme'
import { mountWithPlugins } from '@/tests/utils'

import AppHeader from './AppHeader.vue'

vi.stubGlobal('matchMedia', () => ({ matches: false, addEventListener: vi.fn() }))

afterEach(() => localStorage.clear())

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
  it('renders the brand logo, home link and login button', async () => {
    const { wrapper, router } = mountHeader()
    await router.isReady()

    expect(wrapper.find('[data-test="brand-link"]').text()).toContain('Dayzle')
    expect(wrapper.find('[data-test="home-link"]').text()).toContain('Acasă')
    expect(wrapper.find('[data-test="login-link"]').text()).toContain('Autentificare')
  })

  it('navigates to /login when clicking the login button', async () => {
    const { wrapper, router } = mountHeader()
    await router.isReady()

    await wrapper.find('[data-test="login-link"]').trigger('click')
    await flushPromises()

    expect(router.currentRoute.value.path).toBe('/login')
  })

  it('cycles the theme from its button', async () => {
    const { wrapper, router } = mountHeader()
    await router.isReady()
    const theme = useThemeStore()
    expect(theme.mode).toBe('auto')

    await wrapper.find('[data-test="theme"]').trigger('click')

    expect(theme.mode).toBe('light')
  })

  it('switches the language and remembers it', async () => {
    const { wrapper, router } = mountHeader()
    await router.isReady()
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
