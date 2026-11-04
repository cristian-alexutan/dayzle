import { describe, expect, it } from 'vitest'

import { mountWithPlugins } from '@/tests/utils'

import WordBoard from '../components/WordBoard.vue'
import WordKeyboard from '../components/WordKeyboard.vue'
import type { Guess } from '../types'

const guess: Guess = {
  word: 'câine',
  colors: ['correct', 'absent', 'present', 'absent', 'absent'],
}

function mountBoard(props: Partial<InstanceType<typeof WordBoard>['$props']> = {}) {
  return mountWithPlugins(WordBoard, {
    props: { guesses: [], current: [], rows: 6, length: 5, ...props },
  })
}

describe('WordBoard', () => {
  it('shows 6 rows of 5 tiles', () => {
    const wrapper = mountBoard()

    expect(wrapper.findAll('[data-test="row"]')).toHaveLength(6)
    expect(wrapper.findAll('[data-test="tile"]')).toHaveLength(30)
  })

  it('restores guesses with their colors, without flipping them', () => {
    const tiles = mountBoard({ guesses: [guess] }).findAll('[data-test="tile"]')

    expect(tiles[1]!.text()).toBe('â')
    expect(tiles[0]!.classes()).toContain('word-board__tile--correct')
    expect(tiles[2]!.classes()).toContain('word-board__tile--present')
    expect(tiles[1]!.classes()).toContain('word-board__tile--absent')
    expect(tiles[0]!.classes()).not.toContain('word-board__tile--reveal')
  })

  it('shows the letters being typed on the next free row', () => {
    const tiles = mountBoard({ guesses: [guess], current: ['c', 'a'] }).findAll(
      '[data-test="tile"]',
    )

    expect(tiles[5]!.text()).toBe('c')
    expect(tiles[6]!.text()).toBe('a')
    expect(tiles[7]!.text()).toBe('')
    expect(tiles[5]!.classes()).toContain('word-board__tile--filled')
  })

  it('flips only the row that was just guessed', () => {
    const wrapper = mountBoard({ guesses: [guess, guess], revealRow: 1 })
    const rows = wrapper.findAll('[data-test="row"]')

    expect(rows[0]!.find('.word-board__tile--reveal').exists()).toBe(false)
    expect(rows[1]!.findAll('.word-board__tile--reveal')).toHaveLength(5)
  })

  it('shakes the row being typed', () => {
    const rows = mountBoard({ guesses: [guess], shake: true }).findAll('[data-test="row"]')

    expect(rows[0]!.classes()).not.toContain('word-board__row--shake')
    expect(rows[1]!.classes()).toContain('word-board__row--shake')
  })
})

describe('WordKeyboard', () => {
  it('has the 31 letters, Enter and Backspace', () => {
    const wrapper = mountWithPlugins(WordKeyboard, { props: { colors: {} } })

    expect(wrapper.findAll('button')).toHaveLength(33)
    for (const letter of ['ă', 'â', 'î', 'ș', 'ț']) {
      expect(wrapper.find(`[data-test="key-${letter}"]`).exists()).toBe(true)
    }
  })

  it('emits the key that was pressed', async () => {
    const wrapper = mountWithPlugins(WordKeyboard, { props: { colors: {} } })

    await wrapper.find('[data-test="key-ș"]').trigger('click')
    await wrapper.find('[data-test="enter"]').trigger('click')
    await wrapper.find('[data-test="backspace"]').trigger('click')

    expect(wrapper.emitted('letter')).toEqual([['ș']])
    expect(wrapper.emitted('enter')).toHaveLength(1)
    expect(wrapper.emitted('backspace')).toHaveLength(1)
  })

  it('colors keys by their best color', () => {
    const wrapper = mountWithPlugins(WordKeyboard, {
      props: { colors: { c: 'correct', a: 'present', t: 'absent' } },
    })

    expect(wrapper.find('[data-test="key-c"]').classes()).toContain('word-keyboard__key--correct')
    expect(wrapper.find('[data-test="key-a"]').classes()).toContain('word-keyboard__key--present')
    expect(wrapper.find('[data-test="key-t"]').classes()).toContain('word-keyboard__key--absent')
    expect(wrapper.find('[data-test="key-b"]').classes()).not.toContain(
      'word-keyboard__key--absent',
    )
  })
})
