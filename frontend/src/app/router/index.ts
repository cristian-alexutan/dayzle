import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import { geoRoutes } from '@/features/geo'
import { logicRoutes } from '@/features/logic'
import { mathRoutes } from '@/features/math'
import { wordRoutes } from '@/features/word'

export const appRoutes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
  },
  ...wordRoutes,
  ...mathRoutes,
  ...logicRoutes,
  {
    path: '/games/trivia',
    name: 'trivia',
    component: () => import('../views/GamePlaceholderView.vue'),
    props: { gameKey: 'trivia' },
  },
  ...geoRoutes,
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: appRoutes,
})

export default router
