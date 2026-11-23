// Thin wrappers over the HTTP client for the Trivia feature.
import { http } from '@/api/http'

import type { GameDay, TriviaGame } from '../types'

export function fetchGame(day: GameDay) {
  return http.get<TriviaGame>(`/games/trivia/${day}/`)
}

export function sendAnswer(day: GameDay, question: number, choice: number) {
  return http.post<TriviaGame>(`/games/trivia/${day}/answer/`, { question, choice })
}

/** 50/50 on the current question (409 `nothing_to_hint` if it already had its hint). */
export function sendHint(day: GameDay) {
  return http.post<TriviaGame>(`/games/trivia/${day}/hint/`)
}

export function sendHeartbeat(day: GameDay) {
  return http.post<void>(`/results/trivia/${day}/heartbeat/`)
}
