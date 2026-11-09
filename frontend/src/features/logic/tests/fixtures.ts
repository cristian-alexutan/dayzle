import type { LogicGame } from '../types'

/** A 2 × 2 game in progress; tests override what they need. */
export function makeGame(overrides: Partial<LogicGame> = {}): LogicGame {
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
    solved: null,
    score: null,
    duration_ms: null,
    elapsed_ms: 0,
    ...overrides,
  }
}
