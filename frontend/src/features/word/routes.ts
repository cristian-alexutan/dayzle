// Routes of the Word feature.
import type { RouteRecordRaw } from 'vue-router'

export const wordRoutes: RouteRecordRaw[] = [
  {
    path: '/games/word',
    name: 'word',
    component: () => import('./views/WordGameView.vue'),
  },
]
