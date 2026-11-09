import { createRouter, createWebHistory } from 'vue-router'

import { geoRoutes } from '@/features/geo'
import { logicRoutes } from '@/features/logic'
import { mathRoutes } from '@/features/math'
import { wordRoutes } from '@/features/word'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [...wordRoutes, ...mathRoutes, ...geoRoutes, ...logicRoutes],
})

export default router
