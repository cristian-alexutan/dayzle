import {
  createRouter,
  createWebHistory,
  type Router,
  type RouterHistory,
  type RouteRecordRaw,
} from 'vue-router'

import {
  authRoutes,
  registerAuthGuards,
  sessionKey,
  type SessionReader,
  type SessionState,
} from '@/features/auth'
import { geoRoutes } from '@/features/geo'
import { logicRoutes } from '@/features/logic'
import { mathRoutes } from '@/features/math'
import { wordRoutes } from '@/features/word'

import { appQueryClient } from '../queryClient'

export const appRoutes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
  },
  ...authRoutes,
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

export function createAppRouter(
  history: RouterHistory = createWebHistory(import.meta.env.BASE_URL),
  getSession: SessionReader = () => appQueryClient.getQueryData<SessionState>(sessionKey),
  extraRoutes: RouteRecordRaw[] = [],
): Router {
  const routerInstance = createRouter({
    history,
    routes: [...appRoutes, ...extraRoutes],
  })
  registerAuthGuards(routerInstance, getSession)
  return routerInstance
}

const router = createAppRouter()

export default router
