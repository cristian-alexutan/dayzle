// Thin wrappers over the HTTP client for the Math feature.
import { http } from '@/api/http'

import type { GameDay, MathGame, StepInput } from '../types'

/** Only what the player chose is sent: the server replays the steps and computes every result. */
function toInput(steps: StepInput[]): StepInput[] {
  return steps.map(({ left, op, right }) => ({ left, op, right }))
}

export function fetchGame(day: GameDay) {
  return http.get<MathGame>(`/games/math/${day}/`)
}

export function saveProgress(day: GameDay, steps: StepInput[]) {
  return http.post<MathGame>(`/games/math/${day}/progress/`, { steps: toInput(steps) })
}

export function submitGame(day: GameDay, steps: StepInput[]) {
  return http.post<MathGame>(`/games/math/${day}/submit/`, { steps: toInput(steps) })
}

/** Keeps the server's clock running while the game is visible; see useHeartbeat. */
export function sendHeartbeat(day: GameDay) {
  return http.post<void>(`/results/math/${day}/heartbeat/`)
}
