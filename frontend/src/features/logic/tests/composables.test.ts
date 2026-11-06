import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { effectScope, nextTick, ref } from 'vue'

import { MARKS_SAVE_DELAY_MS, useBoardState } from '../composables/useBoardState'
import { useConflicts, WRONG_SUN_MS } from '../composables/useConflicts'
import { useElapsedTime } from '../composables/useElapsedTime'
import type { Cell, LogicGame } from '../types'

function makeGame(overrides: Partial<LogicGame> = {}): LogicGame {
  return {
    date: '2026-11-05',
    status: 'in_progress',
    size: 2,
    regions: [
      [0, 1],
      [0, 1],
    ],
    suns: [],
    marks: [],
    mistakes: 0,
    streak: 0,
    solved: null,
    score: null,
    duration_ms: null,
    elapsed_ms: 0,
    ...overrides,
  }
}

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('useBoardState', () => {
  function setup(game = makeGame()) {
    const scope = effectScope()
    const place = vi.fn()
    const saveMarks = vi.fn()
    const disabled = ref(false)
    const gameRef = ref(game)
    const board = scope.run(() => useBoardState({ game: gameRef, disabled, place, saveMarks }))!
    return { scope, board, place, saveMarks, disabled, gameRef }
  }

  it('marks an empty cell with an X on the first tap', () => {
    const { board, place } = setup()

    board.tap([0, 0])

    expect(board.contentOf([0, 0])).toBe('mark')
    expect(place).not.toHaveBeenCalled()
  })

  it('places a sun on the second tap', () => {
    const { board, place } = setup()

    board.tap([0, 0])
    board.tap([0, 0])

    expect(place).toHaveBeenCalledWith([0, 0])
    expect(board.contentOf([0, 0])).toBe('empty')
  })

  it('shows the suns from the server and ignores taps on them', () => {
    const { board, place } = setup(makeGame({ suns: [[1, 1]] }))

    board.tap([1, 1])

    expect(board.contentOf([1, 1])).toBe('sun')
    expect(place).not.toHaveBeenCalled()
  })

  it('restores the marks saved on the server', () => {
    const { board } = setup(makeGame({ marks: [[0, 1]] }))

    expect(board.contentOf([0, 1])).toBe('mark')
  })

  it('saves the marks once, a moment after the last tap', () => {
    const { board, saveMarks } = setup()

    board.tap([0, 0])
    board.tap([1, 0])
    vi.advanceTimersByTime(MARKS_SAVE_DELAY_MS - 1)
    expect(saveMarks).not.toHaveBeenCalled()

    vi.advanceTimersByTime(1)
    expect(saveMarks).toHaveBeenCalledTimes(1)
    expect(saveMarks).toHaveBeenCalledWith([
      [0, 0],
      [1, 0],
    ])
  })

  it('saves unsaved marks right away when the page closes', () => {
    const { scope, board, saveMarks } = setup()

    board.tap([0, 0])
    scope.stop()

    expect(saveMarks).toHaveBeenCalledWith([[0, 0]])
  })

  it('ignores taps while disabled', () => {
    const { board, disabled } = setup()
    disabled.value = true

    board.tap([0, 0])

    expect(board.contentOf([0, 0])).toBe('empty')
  })

  it('keeps its own marks when a newer game arrives from the server', async () => {
    const { board, gameRef } = setup()
    board.tap([0, 0])

    gameRef.value = makeGame({ suns: [[1, 1]] })
    await nextTick()

    expect(board.contentOf([0, 0])).toBe('mark')
    expect(board.contentOf([1, 1])).toBe('sun')
  })
})

describe('useConflicts', () => {
  it('shows a wrong sun and its conflicts for a moment', () => {
    const scope = effectScope()
    const conflicts = scope.run(() => useConflicts())!
    const wrong: Cell = [0, 3]

    conflicts.show(wrong, [[0, 2]])

    expect(conflicts.isWrong(wrong)).toBe(true)
    expect(conflicts.isConflict([0, 2])).toBe(true)
    expect(conflicts.isConflict([1, 1])).toBe(false)

    vi.advanceTimersByTime(WRONG_SUN_MS)
    expect(conflicts.isWrong(wrong)).toBe(false)
    expect(conflicts.isConflict([0, 2])).toBe(false)
    scope.stop()
  })
})

describe('useElapsedTime', () => {
  it('counts up from the server time while running', () => {
    const scope = effectScope()
    const running = ref(true)
    const elapsed = scope.run(() => useElapsedTime(5000, running))!

    vi.advanceTimersByTime(3000)
    expect(elapsed.value).toBe(8000)

    running.value = false
    expect(elapsed.value).toBe(5000)
    scope.stop()
  })

  it('starts again from each new server time', async () => {
    const scope = effectScope()
    const serverMs = ref(0)
    const elapsed = scope.run(() => useElapsedTime(serverMs, true))!

    vi.advanceTimersByTime(4000)
    serverMs.value = 10_000
    await nextTick()

    expect(elapsed.value).toBe(10_000)
    scope.stop()
  })
})
