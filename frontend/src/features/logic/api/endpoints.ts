// Thin wrappers over the HTTP client for the Logic feature.
import { http } from '@/api/http'

import type { Cell, GameDay, LogicGame, PlaceResult } from '../types'

export function fetchGame(day: GameDay) {
  return http.get<LogicGame>(`/games/logic/${day}/`)
}

export function placeSun(day: GameDay, [row, col]: Cell) {
  return http.post<PlaceResult>(`/games/logic/${day}/place/`, { row, col })
}

export function saveMarks(day: GameDay, marks: Cell[]) {
  return http.post<LogicGame>(`/games/logic/${day}/marks/`, { marks })
}

export function sendHeartbeat(day: GameDay) {
  return http.post<void>(`/results/logic/${day}/heartbeat/`)
}
