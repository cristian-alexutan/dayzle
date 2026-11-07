import { flushPromises } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import { mountWithPlugins } from '@/tests/utils'

import HomeView from './HomeView.vue'

afterEach(() => localStorage.clear())

function mountHome() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: HomeView },
      { path: '/games/word', component: { template: '<div />' } },
      { path: '/games/logic', component: { template: '<div />' } },
      { path: '/games/math', component: { template: '<div />' } },
      { path: '/games/trivia', component: { template: '<div />' } },
      { path: '/games/geo', component: { template: '<div />' } },
    ],
  })
  return {
    router,
    wrapper: mountWithPlugins(HomeView, {
      global: { plugins: [router] },
    }),
  }
}

describe('HomeView', () => {
  it('renders cards for all five daily games with titles and descriptions', async () => {
    const { wrapper, router } = mountHome()
    await router.isReady()

    const expectedGames = [
      { key: 'word', title: 'Cuvântăl', path: '/games/word' },
      { key: 'logic', title: 'Sunspots', path: '/games/logic' },
      { key: 'math', title: 'Numărăl', path: '/games/math' },
      { key: 'trivia', title: 'Trivia', path: '/games/trivia' },
      { key: 'geo', title: 'ClujGuesser', path: '/games/geo' },
    ]

    for (const game of expectedGames) {
      const card = wrapper.find(`[data-test="game-card-${game.key}"]`)
      expect(card.exists()).toBe(true)

      const link = wrapper.find(`[data-test="game-link-${game.key}"]`)
      expect(link.text()).toBe(game.title)
      expect(link.attributes('href')).toBe(game.path)

      const description = wrapper.find(`[data-test="game-description-${game.key}"]`)
      expect(description.text().length).toBeGreaterThan(10)
    }
  })

  it('navigates to the selected game when clicking its Play button', async () => {
    const { wrapper, router } = mountHome()
    await router.isReady()

    await wrapper.find('[data-test="game-play-word"]').trigger('click')
    await flushPromises()

    expect(router.currentRoute.value.path).toBe('/games/word')
  })
})
