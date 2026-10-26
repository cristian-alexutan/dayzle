import Aura from '@primeuix/themes/aura'
import { VueQueryPlugin } from '@tanstack/vue-query'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import { createApp } from 'vue'

import App from './App.vue'
import { createAppI18n } from './i18n'
import { createAppQueryClient } from './queryClient'
import router from './router'
import './styles/main.css'

createApp(App)
  .use(createPinia())
  .use(VueQueryPlugin, { queryClient: createAppQueryClient() })
  .use(createAppI18n())
  .use(PrimeVue, { theme: { preset: Aura } })
  .use(router)
  .mount('#app')
