// Routes of the Trivia feature.
import type { RouteRecordRaw } from 'vue-router'

export const triviaRoutes: RouteRecordRaw[] = [
  {
    path: '/games/trivia',
    name: 'trivia',
    component: () => import('./views/TriviaGameView.vue'),
  },
]
