import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

import { DARK_MODE_CLASS, useThemeStore } from './theme'

function stubSystemTheme(matches: boolean) {
  vi.stubGlobal('matchMedia', () => ({ matches, addEventListener: vi.fn() }))
}

const hasDarkClass = () => document.documentElement.classList.contains(DARK_MODE_CLASS)

beforeEach(() => {
  setActivePinia(createPinia())
  localStorage.clear()
})

afterEach(() => {
  vi.unstubAllGlobals()
  document.documentElement.classList.remove(DARK_MODE_CLASS)
})

describe('theme store', () => {
  it('starts on auto and follows the system setting', () => {
    stubSystemTheme(true)

    expect(useThemeStore().mode).toBe('auto')
    expect(hasDarkClass()).toBe(true)
  })

  it('cycles light, dark, auto and applies the class', async () => {
    stubSystemTheme(false)
    const theme = useThemeStore()

    theme.cycle()
    await nextTick()
    expect(theme.mode).toBe('light')
    expect(hasDarkClass()).toBe(false)

    theme.cycle()
    await nextTick()
    expect(theme.mode).toBe('dark')
    expect(hasDarkClass()).toBe(true)

    theme.cycle()
    await nextTick()
    expect(theme.mode).toBe('auto')
    expect(hasDarkClass()).toBe(false)
  })

  it('remembers the choice', () => {
    stubSystemTheme(false)
    useThemeStore().cycle()

    setActivePinia(createPinia())

    expect(useThemeStore().mode).toBe('light')
  })
})
