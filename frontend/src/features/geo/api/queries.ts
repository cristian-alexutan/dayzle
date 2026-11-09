// TanStack Query hooks for the GeoGuesser feature.
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, toValue, type MaybeRefOrGetter } from 'vue'

import { useHeartbeat } from '@/shared/composables/useHeartbeat'

import type { GameDay, GuessInput, RegionKey } from '../types'
import { fetchGame, fetchRegions, sendGuess, sendHeartbeat } from './endpoints'

const gameKey = (day: GameDay, region: RegionKey) => ['geo', 'game', day, region ?? 'default']

export { errorCode, errorDetails } from '@/api/http'

/** The regions players can choose, loaded only while `enabled`. */
export function useRegionsQuery(enabled: MaybeRefOrGetter<boolean> = true) {
  return useQuery({
    queryKey: ['geo', 'regions'],
    queryFn: fetchRegions,
    enabled: computed(() => toValue(enabled)),
  })
}

/** The player's game in `region` (the default region when undefined); reloads when it changes. */
export function useGeoGameQuery(day: GameDay, region?: MaybeRefOrGetter<RegionKey>) {
  return useQuery({
    queryKey: computed(() => gameKey(day, toValue(region))),
    queryFn: () => fetchGame(day, toValue(region)),
  })
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
export function useGuessMutation(day: GameDay, region?: MaybeRefOrGetter<RegionKey>) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: GuessInput) => sendGuess(day, input, toValue(region)),
    onMutate: () => {
      const key = gameKey(day, toValue(region))
      return queryClient.cancelQueries({ queryKey: key }).then(() => ({ key }))
    },
    onSuccess: async (game, _input, context) => {
      // The key the guess was sent with, even if the region changed meanwhile.
      const key = context?.key ?? gameKey(day, toValue(region))
      await queryClient.cancelQueries({ queryKey: key })
      queryClient.setQueryData(key, game)
    },
  })
}

/** Count looking around as active: a heartbeat every 15 s while `active` and the page is visible. */
export function useGeoHeartbeat(day: GameDay, active: MaybeRefOrGetter<boolean>) {
  useHeartbeat(() => sendHeartbeat(day), active)
}
