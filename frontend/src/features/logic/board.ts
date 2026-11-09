// Pure helpers for the board, shared by the API cache and the composables of this feature.
import type { Cell, CellChange, CellContent, LogicGame } from './types'

export const sameCell = (a: Cell, b: Cell) => a[0] === b[0] && a[1] === b[1]

export function contentOf(game: LogicGame | undefined, cell: Cell): CellContent {
  if (game?.suns.some((sun) => sameCell(sun, cell))) return 'sun'
  if (game?.marks.some((mark) => sameCell(mark, cell))) return 'mark'
  return 'empty'
}

/**
 * The board as it will look once the server accepts the change, so the screen doesn't wait for
 * it. A sun the server rejects is taken off again when its answer arrives.
 */
export function withChange(game: LogicGame, { cell, content }: CellChange): LogicGame {
  const suns = game.suns.filter((sun) => !sameCell(sun, cell))
  const marks = game.marks.filter((mark) => !sameCell(mark, cell))
  if (content === 'sun') suns.push(cell)
  if (content === 'mark') marks.push(cell)
  return { ...game, suns, marks }
}
