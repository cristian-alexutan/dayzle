import { describe, expect, it } from 'vitest'

import { mountWithPlugins } from '@/tests/utils'

import GameShell from './GameShell.vue'

describe('GameShell', () => {
  it('shows the title and the game', () => {
    const wrapper = mountWithPlugins(GameShell, {
      props: { title: 'Joc' },
      slots: { default: 'board' },
    })

    expect(wrapper.find('h1').text()).toBe('Joc')
    expect(wrapper.text()).toContain('board')
    expect(wrapper.classes()).not.toContain('game-shell--wide')
  })

  it('lets a game draw its own title', () => {
    const wrapper = mountWithPlugins(GameShell, {
      props: { title: 'Joc' },
      slots: { title: '<span class="logo">J*c</span>' },
    })

    expect(wrapper.find('h1 .logo').text()).toBe('J*c')
  })

  it('gives a wide game more room', () => {
    const wrapper = mountWithPlugins(GameShell, { props: { title: 'Joc', wide: true } })

    expect(wrapper.classes()).toContain('game-shell--wide')
  })
})
