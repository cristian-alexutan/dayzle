import { describe, expect, it, vi } from 'vitest'
import { nextTick, ref } from 'vue'

import { boardTiles, checkStep, closestSoFar, useMathBoard } from '../composables/useMathBoard'
import type { PlayedStep } from '../types'

const NUMBERS = [1, 2, 3, 25, 50, 100]

const values = (tiles: { value: number }[]) => tiles.map((tile) => tile.value)

function setup(steps: PlayedStep[] = [], disabled = false) {
  const onStep = vi.fn()
  const saved = ref(steps)
  const board = useMathBoard({
    numbers: NUMBERS,
    steps: saved,
    disabled: () => disabled,
    onStep,
  })
  const tile = (value: number) => board.tiles.value.find((candidate) => candidate.value === value)!
  return { board, onStep, saved, tile }
}

describe('boardTiles', () => {
  it('starts with the 6 numbers in order', () => {
    expect(values(boardTiles(NUMBERS, []))).toEqual(NUMBERS)
  })

  it('removes the numbers a step used and adds its result at the end, as computed', () => {
    const tiles = boardTiles(NUMBERS, [{ left: 100, op: '*', right: 2, result: 200 }])

    expect(values(tiles)).toEqual([1, 3, 25, 50, 200])
    expect(tiles[tiles.length - 1]).toEqual({ id: 's0', value: 200, computed: true })
  })

  it('uses up a starting copy first when a value is also computed', () => {
    const steps: PlayedStep[] = [
      { left: 3, op: '-', right: 1, result: 2 },
      { left: 2, op: '+', right: 25, result: 27 },
    ]

    const tiles = boardTiles(NUMBERS, steps)

    expect(tiles.filter((tile) => tile.value === 2)).toEqual([
      { id: 's0', value: 2, computed: true },
    ])
  })

  it('keeps repeated starting numbers apart', () => {
    const tiles = boardTiles([2, 2, 3, 3, 4, 4], [{ left: 2, op: '*', right: 3, result: 6 }])

    expect(values(tiles)).toEqual([2, 3, 4, 4, 6])
    expect(new Set(tiles.map((tile) => tile.id)).size).toBe(tiles.length)
  })
})

describe('closestSoFar', () => {
  it('is null before the first step, even if a starting number is near the target', () => {
    expect(closestSoFar(boardTiles(NUMBERS, []), 99)).toBeNull()
  })

  it('picks the computed number nearest to the target', () => {
    const steps: PlayedStep[] = [
      { left: 100, op: '*', right: 2, result: 200 },
      { left: 50, op: '+', right: 3, result: 53 },
    ]

    expect(closestSoFar(boardTiles(NUMBERS, steps), 60)).toBe(53)
  })

  it('picks the smaller one on a tie, as the server does', () => {
    const steps: PlayedStep[] = [
      { left: 50, op: '+', right: 1, result: 51 },
      { left: 25, op: '*', right: 2, result: 50 },
      { left: 50, op: '+', right: 3, result: 53 },
    ]

    // 51 and 53 are both 1 away from 52.
    expect(closestSoFar(boardTiles(NUMBERS, steps), 52)).toBe(51)
  })

  it('ignores a computed number that a later step used up', () => {
    const steps: PlayedStep[] = [
      { left: 100, op: '+', right: 1, result: 101 },
      { left: 101, op: '*', right: 2, result: 202 },
    ]

    expect(closestSoFar(boardTiles(NUMBERS, steps), 100)).toBe(202)
  })
})

describe('checkStep', () => {
  it.each([
    [{ left: 3, op: '-', right: 3 }, 'not_positive'],
    [{ left: 2, op: '-', right: 3 }, 'not_positive'],
    [{ left: 53, op: '/', right: 25 }, 'not_whole'],
    [{ left: 50, op: '/', right: 25 }, null],
    [{ left: 3, op: '-', right: 2 }, null],
    [{ left: 2, op: '+', right: 3 }, null],
    [{ left: 2, op: '*', right: 3 }, null],
  ] as const)('%o is %s', (step, reason) => {
    expect(checkStep(step)).toBe(reason)
  })
})

describe('useMathBoard', () => {
  it('plays a number, an operator and a second number as one step', () => {
    const { board, onStep, tile } = setup()

    board.selectTile(tile(100).id)
    board.selectOperator('*')
    board.selectTile(tile(2).id)

    expect(onStep).toHaveBeenCalledWith({ left: 100, op: '*', right: 2 })
  })

  it('keeps the picks until the server saves the step, so a failed save is easy to retry', async () => {
    const { board, saved, tile } = setup()
    board.selectTile(tile(100).id)
    board.selectOperator('*')
    board.selectTile(tile(2).id)

    expect(board.firstId.value).toBe(tile(100).id)
    expect(board.operator.value).toBe('*')

    saved.value = [{ left: 100, op: '*', right: 2, result: 200 }]
    await nextTick()

    expect(board.firstId.value).toBeNull()
    expect(board.operator.value).toBeNull()
  })

  it('unpicks a number tapped twice, and switches to another before an operator', () => {
    const { board, tile } = setup()

    board.selectTile(tile(100).id)
    board.selectTile(tile(100).id)
    expect(board.firstId.value).toBeNull()

    board.selectTile(tile(100).id)
    board.selectTile(tile(50).id)
    expect(board.firstId.value).toBe(tile(50).id)
  })

  it('ignores an operator before a number, and toggles one tapped twice', () => {
    const { board, tile } = setup()

    board.selectOperator('+')
    expect(board.operator.value).toBeNull()

    board.selectTile(tile(3).id)
    board.selectOperator('+')
    board.selectOperator('+')
    expect(board.operator.value).toBeNull()
  })

  it('refuses a step that would not give a positive whole number and keeps the choice', () => {
    const { board, onStep, tile } = setup()

    board.selectTile(tile(3).id)
    board.selectOperator('/')
    board.selectTile(tile(2).id)

    expect(onStep).not.toHaveBeenCalled()
    expect(board.refusal.value).toEqual({
      reason: 'not_whole',
      step: { left: 3, op: '/', right: 2 },
      tileId: tile(2).id,
    })
    expect(board.firstId.value).toBe(tile(3).id)
    expect(board.operator.value).toBe('/')
  })

  it('clears the refusal when the player changes the operator', () => {
    const { board, onStep, tile } = setup()
    board.selectTile(tile(2).id)
    board.selectOperator('-')
    board.selectTile(tile(3).id)

    board.selectOperator('+')
    expect(board.refusal.value).toBeNull()

    board.selectTile(tile(3).id)
    expect(onStep).toHaveBeenCalledWith({ left: 2, op: '+', right: 3 })
  })

  it('does nothing while disabled', () => {
    const { board, tile } = setup([], true)

    board.selectTile(tile(100).id)

    expect(board.firstId.value).toBeNull()
  })

  it('drops the choice when the saved steps change', async () => {
    const { board, saved, tile } = setup()
    board.selectTile(tile(25).id)

    saved.value = [{ left: 100, op: '*', right: 2, result: 200 }]
    await nextTick()

    expect(board.firstId.value).toBeNull()
    expect(values(board.tiles.value)).toEqual([1, 3, 25, 50, 200])
  })
})
