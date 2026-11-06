import { createRouter, createWebHistory } from 'vue-router'

import { logicRoutes } from '@/features/logic'
import { wordRoutes } from '@/features/word'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [...wordRoutes, ...logicRoutes],
})

export default router
