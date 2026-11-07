// Routes of the Auth (Google login, guest identity, route guards) feature.
import type { RouteRecordRaw } from 'vue-router'

export const authRoutes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('./views/AuthView.vue'),
    meta: { guestOnly: true },
  },
]
