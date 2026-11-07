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
  })
})
