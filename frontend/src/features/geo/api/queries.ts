// TanStack Query hooks for the GeoGuesser feature.
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import type { MaybeRefOrGetter } from 'vue'

import { useHeartbeat } from '@/shared/composables/useHeartbeat'

import type { GameDay, GuessInput, RegionKey } from '../types'
import { fetchGame, fetchRegions, sendGuess, sendHeartbeat } from './endpoints'

const gameKey = (day: GameDay, region: RegionKey) => ['geo', 'game', day, region ?? 'default']

export { errorCode, errorDetails } from '@/api/http'

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
 *
 * A reload of the game that is running when the guess is sent, or starts while it is on its way,
 * is cancelled: finishing afterwards, it would bring back the round just guessed, and the next
 * guess would be refused.
 */
export function useGuessMutation(day: GameDay, region?: RegionKey) {
  const queryClient = useQueryClient()
  const cancelReloads = () => queryClient.cancelQueries({ queryKey: gameKey(day, region) })
  return useMutation({
    mutationFn: (input: GuessInput) => sendGuess(day, input, region),
    onMutate: cancelReloads,
    onSuccess: async (game) => {
      await cancelReloads()
      queryClient.setQueryData(gameKey(day, region), game)
    },
  })
}

/** Count looking around as active: a heartbeat every 15 s while `active` and the page is visible. */
export function useGeoHeartbeat(day: GameDay, active: MaybeRefOrGetter<boolean>) {
  useHeartbeat(() => sendHeartbeat(day), active)
}
