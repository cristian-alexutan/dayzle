import { VueQueryPlugin } from '@tanstack/vue-query'
import { createPinia } from 'pinia'
import 'primeicons/primeicons.css'
import PrimeVue from 'primevue/config'
import { createApp } from 'vue'

import { DARK_MODE_CLASS } from '@/shared/stores/theme'

import App from './App.vue'
import { createAppI18n } from './i18n'
import { appQueryClient } from './queryClient'
import router from './router'
import './styles/theme.css'
import './styles/main.css'
import { DayzlePreset } from './theme/preset'

createApp(App)
  .use(createPinia())
  .use(VueQueryPlugin, { queryClient: appQueryClient })
  .use(createAppI18n())
  .use(PrimeVue, {
    theme: { preset: DayzlePreset, options: { darkModeSelector: `.${DARK_MODE_CLASS}` } },
  })
  .use(router)
  .mount('#app')
