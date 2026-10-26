import { createI18n } from 'vue-i18n'

import en from '@/locales/en.json'
import ro from '@/locales/ro.json'

export function createAppI18n() {
  return createI18n({
    legacy: false,
    locale: 'ro',
    fallbackLocale: 'en',
    messages: { ro, en },
  })
}
