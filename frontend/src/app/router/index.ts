import { createRouter, createWebHistory } from 'vue-router'

import { mathRoutes } from '@/features/math'
import { wordRoutes } from '@/features/word'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [...wordRoutes, ...mathRoutes],
})

export default router
