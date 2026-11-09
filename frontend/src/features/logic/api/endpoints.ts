// Thin wrappers over the HTTP client for the Logic feature.
import { http } from '@/api/http'

import type { CellChange, CellResult, GameDay, LogicGame } from '../types'

export function fetchGame(day: GameDay) {
  return http.get<LogicGame>(`/games/logic/${day}/`)
}

export function setCell(day: GameDay, { cell: [row, col], content }: CellChange) {
  return http.post<CellResult>(`/games/logic/${day}/cell/`, { row, col, content })
}

export function clearBoard(day: GameDay) {
  return http.post<LogicGame>(`/games/logic/${day}/clear/`)
}

export function sendHeartbeat(day: GameDay) {
  return http.post<void>(`/results/logic/${day}/heartbeat/`)
}
