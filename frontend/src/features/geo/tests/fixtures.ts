import type { GeoGame, Region } from '../types'

export const cluj: Region = {
  key: 'cluj-napoca',
  name: 'Cluj-Napoca',
  bounds: { south: 46.72, west: 23.5, north: 46.82, east: 23.7 },
}

export const newGame: GeoGame = {
  date: '2026-11-08',
  region: cluj,
  status: 'in_progress',
  rounds: 5,
  current_round: 1,
  panorama_id: 'pano-1',
  results: [],
  total_score: 0,
  max_score: 5000,
  solved: null,
  duration_ms: null,
}

const guessedRound = (round: number) => ({
  round,
  guess: { lat: 46.77, lng: 23.6 },
  location: { lat: 46.771, lng: 23.59 },
  distance_m: 780,
  score: 594,
})

export const afterFirstGuess: GeoGame = {
  ...newGame,
  current_round: 2,
  panorama_id: 'pano-2',
  results: [guessedRound(1)],
  total_score: 594,
}

export const finishedGame: GeoGame = {
  ...newGame,
  status: 'completed',
  current_round: null,
  panorama_id: null,
  results: [1, 2, 3, 4, 5].map(guessedRound),
  total_score: 2970,
  solved: true,
  duration_ms: 95000,
}

export function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

export function errorResponse(status: number, code: string, details: unknown = null) {
  return jsonResponse(status, { error: { code, message: code, details } })
}
