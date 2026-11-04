import { createRouter, createWebHistory } from 'vue-router'

import { wordRoutes } from '@/features/word'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [...wordRoutes],
})

export default router
