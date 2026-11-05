// Thin wrappers over the HTTP client for the Word feature.
import { http } from '@/api/http'

import type { GameDay, WordGame } from '../types'

export function fetchGame(day: GameDay) {
  return http.get<WordGame>(`/games/word/${day}/`)
}

export function sendGuess(day: GameDay, guess: string) {
  return http.post<WordGame>(`/games/word/${day}/guess/`, { guess })
}

export function sendHeartbeat(day: GameDay) {
  return http.post<void>(`/results/word/${day}/heartbeat/`)
}
