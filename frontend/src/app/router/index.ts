import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import { authRoutes } from '@/features/auth'
import { mathRoutes } from '@/features/math'
import { wordRoutes } from '@/features/word'

export const appRoutes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
  },
  ...authRoutes,
  ...wordRoutes,
  ...mathRoutes,
  {
    path: '/games/logic',
    name: 'logic',
    component: () => import('../views/GamePlaceholderView.vue'),
    props: { gameKey: 'logic' },
  },
  {
    path: '/games/trivia',
    name: 'trivia',
    component: () => import('../views/GamePlaceholderView.vue'),
    props: { gameKey: 'trivia' },
  },
  {
    path: '/games/geo',
    name: 'geo',
    component: () => import('../views/GamePlaceholderView.vue'),
    props: { gameKey: 'geo' },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: appRoutes,
})

export default router
