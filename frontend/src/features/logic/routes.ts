// Routes of the Logic feature.
import type { RouteRecordRaw } from 'vue-router'

export const logicRoutes: RouteRecordRaw[] = [
  {
    path: '/games/logic',
    name: 'logic',
    component: () => import('./views/LogicGameView.vue'),
  },
]
