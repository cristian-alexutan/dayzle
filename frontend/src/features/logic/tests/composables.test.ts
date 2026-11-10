import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { effectScope, ref } from 'vue'

import { withChange } from '../board'
import { useBoardState } from '../composables/useBoardState'
import { REJECTED_SUN_MS, useConflicts } from '../composables/useConflicts'
import type { Cell, LogicGame } from '../types'
import { makeGame } from './fixtures'

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('withChange', () => {
  it('puts an X, a sun or nothing on a cell', () => {
    const game = makeGame({ marks: [[0, 0]] })

    expect(withChange(game, { cell: [0, 0], content: 'sun' })).toMatchObject({
      suns: [[0, 0]],
      marks: [],
    })
    expect(withChange(game, { cell: [1, 1], content: 'mark' }).marks).toEqual([
      [0, 0],
      [1, 1],
    ])
    expect(withChange(game, { cell: [0, 0], content: 'empty' }).marks).toEqual([])
  })
})

describe('useBoardState', () => {
  function setup(game: LogicGame = makeGame()) {
    const gameRef = ref(game)
    const change = vi.fn((c) => (gameRef.value = withChange(gameRef.value, c)))
    const disabled = ref(false)
    const scope = effectScope()
    const board = scope.run(() => useBoardState({ game: gameRef, disabled, change }))!
    return { board, change, disabled, gameRef }
  }

  it('cycles a cell: empty, X, sun, empty', () => {
    const { board, change } = setup()

    board.tap([0, 0])
    expect(board.contentOf([0, 0])).toBe('mark')
    board.tap([0, 0])
    expect(board.contentOf([0, 0])).toBe('sun')
    board.tap([0, 0])
    expect(board.contentOf([0, 0])).toBe('empty')

    expect(change.mock.calls.map(([c]) => c.content)).toEqual(['mark', 'sun', 'empty'])
  })

  it('undoes changes one by one, putting back what the cell held', () => {
    const { board } = setup()
    board.tap([0, 0])
    board.tap([0, 0])
    board.tap([1, 1])

    board.undo()
    expect(board.contentOf([1, 1])).toBe('empty')
    board.undo()
    expect(board.contentOf([0, 0])).toBe('mark')
    board.undo()
    expect(board.contentOf([0, 0])).toBe('empty')
    expect(board.canUndo.value).toBe(false)
  })

  it('forgets a rejected sun, so undo skips it', () => {
    const { board, gameRef } = setup()
    board.tap([0, 0]) // X
    board.tap([0, 0]) // sun, which the server rejects:
    gameRef.value = makeGame({ marks: [[0, 0]], mistakes: 1 })
    board.forget([0, 0])

    board.undo()

    expect(board.contentOf([0, 0])).toBe('empty')
  })

  it('ignores taps and undo while disabled', () => {
    const { board, change, disabled } = setup()
    board.tap([0, 0])
    disabled.value = true

    board.tap([1, 1])
    board.undo()

    expect(change).toHaveBeenCalledTimes(1)
  })

  it('knows when the board is empty', () => {
    const { board } = setup()
    expect(board.isEmpty.value).toBe(true)

    board.tap([0, 0])
    expect(board.isEmpty.value).toBe(false)
  })
})

describe('useConflicts', () => {
  it('shows a rejected sun and its conflicts for a moment', () => {
    const scope = effectScope()
    const conflicts = scope.run(() => useConflicts())!
    const rejected: Cell = [0, 3]

    conflicts.show(rejected, [[0, 2]])

    expect(conflicts.isRejected(rejected)).toBe(true)
    expect(conflicts.isConflict([0, 2])).toBe(true)
    expect(conflicts.isConflict([1, 1])).toBe(false)

    vi.advanceTimersByTime(REJECTED_SUN_MS)
    expect(conflicts.isRejected(rejected)).toBe(false)
    expect(conflicts.isConflict([0, 2])).toBe(false)
    scope.stop()
  })
})
