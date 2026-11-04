import { describe, expect, it } from 'vitest'

import { mountWithPlugins } from '@/tests/utils'

import GameShell from './GameShell.vue'

describe('GameShell', () => {
  it('spells the title in tiles, keeping it readable as one word', () => {
    const wrapper = mountWithPlugins(GameShell, {
      props: { title: 'Joc' },
      slots: { default: 'board' },
    })

    expect(wrapper.findAll('.game-shell__letter').map((letter) => letter.text())).toEqual([
      'J',
      'o',
      'c',
    ])
    expect(wrapper.find('h1').attributes('aria-label')).toBe('Joc')
    expect(wrapper.text()).toContain('board')
  })
})
