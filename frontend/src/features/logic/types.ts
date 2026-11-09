// Types of the Logic feature.
import type { components } from '@/api/generated/schema'

/** A cell of the grid as [row, col], counted from 0. */
export type Cell = [number, number]

/** What a cell shows: nothing, the player's X note, or a sun. */
export type CellContent = components['schemas']['ContentEnum']

/** A change the player makes to one cell. */
export interface CellChange {
  cell: Cell
  content: CellContent
}

/** The player's game. `solved`, `score` and `duration_ms` are null until it ends. */
export type LogicGame = Omit<components['schemas']['LogicGame'], 'suns' | 'marks'> & {
  suns: Cell[]
  marks: Cell[]
}

/** The server's answer to a cell change: whether a new sun was rejected, and the new board. */
export type CellResult = Omit<components['schemas']['CellResult'], 'conflicts' | 'game'> & {
  conflicts: Cell[]
  game: LogicGame
}

/** The day in the URL: `today` or a date such as `2026-11-05`. */
export type GameDay = string
