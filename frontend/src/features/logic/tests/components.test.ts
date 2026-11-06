import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import { mountWithPlugins } from '@/tests/utils'

import LogicBoard from '../components/LogicBoard.vue'
import LogicCell from '../components/LogicCell.vue'
import LogicToolbar from '../components/LogicToolbar.vue'
import LogicTutorial from '../components/LogicTutorial.vue'
import type { Cell, CellContent } from '../types'

const NO_EDGES = { top: false, right: false, bottom: false, left: false }

function mountCell(props: Partial<InstanceType<typeof LogicCell>['$props']> = {}) {
  return mount(LogicCell, {
    props: { region: 2, content: 'empty', edges: NO_EDGES, label: 'cell', ...props },
  })
}

describe('LogicCell', () => {
  it('shows nothing, an X or a sun', () => {
    expect(mountCell().find('i').exists()).toBe(false)
    expect(mountCell({ content: 'mark' }).find('.pi-times').exists()).toBe(true)
    expect(mountCell({ content: 'sun' }).find('.pi-sun').exists()).toBe(true)
  })

  it('takes its color from the region variable', () => {
    const style = mountCell().attributes('style')
    expect(style).toContain('var(--dz-region-2)')
  })

  it('shows a wrong sun and a conflicting one', () => {
    const wrong = mountCell({ wrong: true })
    expect(wrong.find('.pi-sun').exists()).toBe(true)
    expect(wrong.classes()).toContain('logic-cell--wrong')
    expect(mountCell({ content: 'sun', conflict: true }).classes()).toContain(
      'logic-cell--conflict',
    )
  })

  it('emits a tap, unless disabled', async () => {
    const cell = mountCell()
    await cell.trigger('click')
    expect(cell.emitted('tap')).toHaveLength(1)

    expect(mountCell({ disabled: true }).attributes('disabled')).toBeDefined()
  })
})

describe('LogicBoard', () => {
  const regions = [
    [0, 0, 1],
    [2, 0, 1],
    [2, 2, 1],
  ]

  function mountBoard() {
    return mountWithPlugins(LogicBoard, {
      props: {
        regions,
        contentOf: (): CellContent => 'empty',
        isWrong: () => false,
        isConflict: () => false,
      },
    })
  }

  it('draws one cell per square of the grid', () => {
    expect(mountBoard().findAll('[data-test="cell"]')).toHaveLength(9)
  })

  it('draws thick lines only where two regions meet', () => {
    const middle = mountBoard().findAll('[data-test="cell"]')[4]! // (1, 1), region 0
    expect(middle.classes()).toContain('logic-cell--edge-right') // (1, 2) is region 1
    expect(middle.classes()).toContain('logic-cell--edge-bottom') // (2, 1) is region 2
    expect(middle.classes()).toContain('logic-cell--edge-left') // (1, 0) is region 2
    expect(middle.classes()).not.toContain('logic-cell--edge-top') // (0, 1) is region 0
  })

  it('reports which cell was tapped', async () => {
    const board = mountBoard()
    await board.findAll('[data-test="cell"]')[5]!.trigger('click')
    expect(board.emitted('tap')![0]).toEqual([[1, 2] satisfies Cell])
  })
})

describe('LogicToolbar', () => {
  function mountToolbar(props: Partial<InstanceType<typeof LogicToolbar>['$props']> = {}) {
    return mountWithPlugins(LogicToolbar, {
      props: {
        elapsedMs: 83_000,
        mistakes: 2,
        streak: 3,
        canUndo: true,
        hasMarks: true,
        playing: true,
        ...props,
      },
    })
  }

  it('shows the time, the mistakes and the streak', () => {
    const toolbar = mountToolbar()
    expect(toolbar.find('[data-test="time"]').text()).toContain('1:23')
    expect(toolbar.find('[data-test="mistakes"]').text()).toContain('2')
    expect(toolbar.find('[data-test="streak"]').text()).toContain('×3')
  })

  it('emits undo, clear and help', async () => {
    const toolbar = mountToolbar()
    await toolbar.find('[data-test="undo"]').trigger('click')
    await toolbar.find('[data-test="clear"]').trigger('click')
    await toolbar.find('[data-test="help"]').trigger('click')
    expect(toolbar.emitted('undo')).toHaveLength(1)
    expect(toolbar.emitted('clear')).toHaveLength(1)
    expect(toolbar.emitted('help')).toHaveLength(1)
  })

  it('disables the X buttons when there is nothing to undo or clear', () => {
    const toolbar = mountToolbar({ canUndo: false, hasMarks: false })
    expect(toolbar.find('[data-test="undo"]').attributes('disabled')).toBeDefined()
    expect(toolbar.find('[data-test="clear"]').attributes('disabled')).toBeDefined()
  })

  it('hides the X buttons once the game is over', () => {
    const toolbar = mountToolbar({ playing: false })
    expect(toolbar.find('[data-test="undo"]').exists()).toBe(false)
    expect(toolbar.find('[data-test="help"]').exists()).toBe(true)
  })
})

describe('LogicTutorial', () => {
  it('shows the rules and closes with its button', async () => {
    const tutorial = mountWithPlugins(LogicTutorial, {
      props: { visible: true },
      attachTo: document.body,
    })
    await flushPromises()

    const dialog = document.body.querySelector('[data-test="tutorial"]')
    expect(dialog?.textContent).toContain('diagonală')
    ;(document.body.querySelector('[data-test="tutorial-start"]') as HTMLElement).click()
    expect(tutorial.emitted('update:visible')![0]).toEqual([false])
    tutorial.unmount()
    document.body.innerHTML = ''
  })
})
