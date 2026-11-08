// Routes of the GeoGuesser feature.
import type { RouteRecordRaw } from 'vue-router'

export const geoRoutes: RouteRecordRaw[] = [
  {
    path: '/games/geo',
    name: 'geo',
    component: () => import('./views/GeoGameView.vue'),
  },
]
