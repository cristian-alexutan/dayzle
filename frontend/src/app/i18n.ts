import { createI18n } from 'vue-i18n'

import en from '@/locales/en.json'
import ro from '@/locales/ro.json'

export type AppLocale = 'ro' | 'en'

const STORAGE_KEY = 'dayzle.locale'

function readStoredLocale(): AppLocale {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'en' ? 'en' : 'ro'
  } catch {
    return 'ro'
  }
}

export function storeLocale(locale: AppLocale) {
  try {
    localStorage.setItem(STORAGE_KEY, locale)
  } catch {
    // The choice just isn't remembered, e.g. in a private window.
  }
}

export function createAppI18n() {
  return createI18n({
    legacy: false,
    locale: readStoredLocale(),
    fallbackLocale: 'en',
    messages: { ro, en },
  })
}
