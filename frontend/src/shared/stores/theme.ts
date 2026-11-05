import { defineStore } from 'pinia'
import { computed, ref, watchEffect } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'auto'

/** Set on <html> when dark mode is on; PrimeVue's darkModeSelector uses it too. */
export const DARK_MODE_CLASS = 'app-dark'

const STORAGE_KEY = 'dayzle.theme'
const MODES: ThemeMode[] = ['light', 'dark', 'auto']

function readStoredMode(): ThemeMode {
  try {
    const stored = localStorage.getItem(STORAGE_KEY) as ThemeMode | null
    return stored && MODES.includes(stored) ? stored : 'auto'
  } catch {
    return 'auto'
  }
}

export const useThemeStore = defineStore('theme', () => {
  const mode = ref<ThemeMode>(readStoredMode())

  const systemPreference = window.matchMedia?.('(prefers-color-scheme: dark)')
  const systemIsDark = ref(systemPreference?.matches ?? false)
  systemPreference?.addEventListener('change', (event) => {
    systemIsDark.value = event.matches
  })

  const isDark = computed(
    () => mode.value === 'dark' || (mode.value === 'auto' && systemIsDark.value),
  )

  watchEffect(() => {
    document.documentElement.classList.toggle(DARK_MODE_CLASS, isDark.value)
  })

  /** Move to the next mode: light, dark, auto, then light again. */
  function cycle() {
    mode.value = MODES[(MODES.indexOf(mode.value) + 1) % MODES.length]!
    try {
      localStorage.setItem(STORAGE_KEY, mode.value)
    } catch {
      // The choice just isn't remembered, e.g. in a private window.
    }
  }

  return { mode, isDark, cycle }
})
