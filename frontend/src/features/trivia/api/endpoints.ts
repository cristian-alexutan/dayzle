// Thin wrappers over the HTTP client for the Trivia feature.
import { http } from '@/api/http'

import type { GameDay, TriviaGame } from '../types'

export function fetchGame(day: GameDay) {
  return http.get<TriviaGame>(`/games/trivia/${day}/`)
}

export function sendAnswer(day: GameDay, question: number, choice: number) {
  return http.post<TriviaGame>(`/games/trivia/${day}/answer/`, { question, choice })
}

export function sendHeartbeat(day: GameDay) {
  return http.post<void>(`/results/trivia/${day}/heartbeat/`)
}
