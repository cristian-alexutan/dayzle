// Thin wrappers over the HTTP client for the GeoGuesser feature.
import { http } from '@/api/http'

import type { GameDay, GeoGame, GuessInput, Region, RegionKey } from '../types'

/** `?region=<key>` when a region is chosen; the backend plays the default region otherwise. */
function regionQuery(region: RegionKey) {
  return region ? `?region=${encodeURIComponent(region)}` : ''
}

export function fetchRegions() {
  return http.get<Region[]>('/games/geo/regions/')
}

/** Opening the game starts it, and its clock, on the first visit of the day. */
export function fetchGame(day: GameDay, region?: RegionKey) {
  return http.get<GeoGame>(`/games/geo/${day}/${regionQuery(region)}`)
}

export function sendGuess(day: GameDay, { round, lat, lng }: GuessInput, region?: RegionKey) {
  return http.post<GeoGame>(`/games/geo/${day}/guess/${regionQuery(region)}`, { round, lat, lng })
}

/** Keeps the server's clock running while the game is visible; see useHeartbeat. */
export function sendHeartbeat(day: GameDay) {
  return http.post<void>(`/results/geo/${day}/heartbeat/`)
}
