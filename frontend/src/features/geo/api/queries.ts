// TanStack Query hooks for the GeoGuesser feature.
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import type { MaybeRefOrGetter } from 'vue'

import { ApiError } from '@/api/http'
import { useHeartbeat } from '@/shared/composables/useHeartbeat'

import type { GameDay, GuessInput, RegionKey } from '../types'
import { fetchGame, fetchRegions, sendGuess, sendHeartbeat } from './endpoints'

const gameKey = (day: GameDay, region: RegionKey) => ['geo', 'game', day, region ?? 'default']

/** The backend's error code (`no_puzzle`, `region_locked`, ...), or null for any other error. */
export function errorCode(error: unknown): string | null {
  return error instanceof ApiError ? error.code : null
}

/** The error's `details`, such as `{ region }` for `region_locked`, or null. */
export function errorDetails(error: unknown): Record<string, unknown> | null {
  if (!(error instanceof ApiError)) return null
  const { details } = error
  return typeof details === 'object' && details !== null
    ? (details as Record<string, unknown>)
    : null
}

export function useRegionsQuery() {
  return useQuery({ queryKey: ['geo', 'regions'], queryFn: fetchRegions })
}

export function useGeoGameQuery(day: GameDay, region?: RegionKey) {
  return useQuery({ queryKey: gameKey(day, region), queryFn: () => fetchGame(day, region) })
}

/**
 * Guess the current round. The response is the whole updated game, with the guessed round's
 * location in `results` and the next panorama, so it replaces the cached one. The fifth guess
 * comes back with `status: 'completed'`, the score and the time.
 */
export function useGuessMutation(day: GameDay, region?: RegionKey) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: GuessInput) => sendGuess(day, input, region),
    onSuccess: (game) => queryClient.setQueryData(gameKey(day, region), game),
  })
}

/** Count looking around as active: a heartbeat every 15 s while `active` and the page is visible. */
export function useGeoHeartbeat(day: GameDay, active: MaybeRefOrGetter<boolean>) {
  useHeartbeat(() => sendHeartbeat(day), active)
}
