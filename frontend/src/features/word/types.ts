// Types of the Word feature.
import type { components } from '@/api/generated/schema'

export type LetterColor = 'correct' | 'present' | 'absent'

export interface Guess {
  word: string
  colors: LetterColor[]
}

/** The player's game. `answer`, `solved`, `score` and `duration_ms` are null until it ends. */
export type WordGame = Omit<components['schemas']['WordGame'], 'guesses'> & { guesses: Guess[] }

/** The day in the URL: `today` or a date such as `2026-10-27`. */
export type GameDay = string
