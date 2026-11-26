// Types of the Math feature.
import type { components } from '@/api/generated/schema'

/** The player's board. Results and the puzzle's secrets (`solution`, ...) are null until it ends. */
export type MathGame = components['schemas']['MathGame']

/** A step after the server computed it. */
export type PlayedStep = components['schemas']['PlayedStep']

/** A step as the player sends it: two numbers and an operator. The server computes the result. */
export type StepInput = components['schemas']['StepInput']

export type Operator = components['schemas']['OpEnum']

/**
 * A hint: `pair` is the two numbers of the board to combine next (the operator stays for the
 * player to find); `restart` is the first step of a solution, when the board can no longer
 * reach the target. Exactly one is set. `game` is the board, with the hint counted.
 */
export type HintResult = components['schemas']['HintResult']

/** How each operator is shown: the API uses `*` and `/`, players see × and ÷. */
export const OPERATOR_SYMBOLS: Record<Operator, string> = { '+': '+', '-': '−', '*': '×', '/': '÷' }

/** The score of an exact finish, the most a game can get (the backend's `rules.score`). */
export const MAX_SCORE = 1000

/** The day in the URL: `today` or a date such as `2026-11-07`. */
export type GameDay = string
