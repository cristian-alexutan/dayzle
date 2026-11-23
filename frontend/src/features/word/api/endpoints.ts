// Thin wrappers over the HTTP client for the Word feature.
import { http } from '@/api/http'

import type { GameDay, WordGame } from '../types'

export function fetchGame(day: GameDay) {
  return http.get<WordGame>(`/games/word/${day}/`)
}

export function sendGuess(day: GameDay, guess: string) {
  return http.post<WordGame>(`/games/word/${day}/guess/`, { guess })
}

/** Reveal a letter of the word not discovered yet (409 `nothing_to_hint` when none is left). */
export function sendHint(day: GameDay) {
  return http.post<WordGame>(`/games/word/${day}/hint/`)
}

export function sendHeartbeat(day: GameDay) {
  return http.post<void>(`/results/word/${day}/heartbeat/`)
}
