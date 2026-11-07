// Routes of the Math feature.
import type { RouteRecordRaw } from 'vue-router'

export const mathRoutes: RouteRecordRaw[] = [
  {
    path: '/games/math',
    name: 'math',
    component: () => import('./views/MathGameView.vue'),
  },
]
