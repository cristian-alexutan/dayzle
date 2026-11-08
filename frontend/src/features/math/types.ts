// Types of the Math feature.
import type { components } from '@/api/generated/schema'

/** The player's board. Results and the puzzle's secrets (`solution`, ...) are null until it ends. */
export type MathGame = components['schemas']['MathGame']

/** A step after the server computed it. */
export type PlayedStep = components['schemas']['PlayedStep']

/** A step as the player sends it: two numbers and an operator. The server computes the result. */
export type StepInput = components['schemas']['StepInput']

export type Operator = components['schemas']['OpEnum']

/** How each operator is shown: the API uses `*` and `/`, players see × and ÷. */
export const OPERATOR_SYMBOLS: Record<Operator, string> = { '+': '+', '-': '−', '*': '×', '/': '÷' }

/** The day in the URL: `today` or a date such as `2026-11-07`. */
export type GameDay = string
