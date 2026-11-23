// Types of the Trivia feature.
import type { components } from '@/api/generated/schema'

/**
 * The player's quiz. `score`, `solved` and `duration_ms` are null until the fifth answer; `score`
 * goes from 0 to 5 in halves (a correct answer after a hint is worth half a point).
 */
export type TriviaGame = components['schemas']['TriviaGame']
/** A question as the player sees it: which choice is correct is never sent before answering. */
export type Question = components['schemas']['Question']
/** An answer the player gave, with the correct choice revealed by the server. */
export type Answer = components['schemas']['Answer']
export type Category = components['schemas']['CategoryEnum']
/** A 50/50 on a question: the two wrong choices it removed. */
export type Hint = components['schemas']['Hint']

/**
 * How a choice is drawn: before answering, or once the server revealed the correct one.
 * `removed` is a wrong choice a hint took away: it can't be picked.
 */
export type ChoiceState = 'idle' | 'correct' | 'wrong' | 'dimmed' | 'removed'

/** The day in the URL: `today` or a date such as `2026-10-27`. */
export type GameDay = string
