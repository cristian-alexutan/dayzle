import { afterEach, describe, expect, it, vi } from 'vitest'

import { useThemeStore } from '@/shared/stores/theme'
import { mountWithPlugins } from '@/tests/utils'

import AppHeader from './AppHeader.vue'

vi.stubGlobal('matchMedia', () => ({ matches: false, addEventListener: vi.fn() }))

afterEach(() => localStorage.clear())

describe('AppHeader', () => {
  it('cycles the theme from its button', async () => {
    const wrapper = mountWithPlugins(AppHeader)
    const theme = useThemeStore()
    expect(theme.mode).toBe('auto')

    await wrapper.find('[data-test="theme"]').trigger('click')

    expect(theme.mode).toBe('light')
  })

  it('switches the language and remembers it', async () => {
    const wrapper = mountWithPlugins(AppHeader)
    const language = wrapper.find('[data-test="language"]')
    expect(language.text()).toBe('RO')

    await language.trigger('click')

    expect(language.text()).toBe('EN')
    expect(document.documentElement.lang).toBe('en')
    expect(localStorage.getItem('dayzle.locale')).toBe('en')
  })
})
