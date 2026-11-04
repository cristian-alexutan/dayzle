// TanStack Query hooks for the Word feature.
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import type { MaybeRefOrGetter } from 'vue'

import { useHeartbeat } from '@/shared/composables/useHeartbeat'

import type { GameDay } from '../types'
import { fetchGame, sendGuess, sendHeartbeat } from './endpoints'

const gameKey = (day: GameDay) => ['word', 'game', day]

export function useWordGameQuery(day: GameDay) {
  return useQuery({ queryKey: gameKey(day), queryFn: () => fetchGame(day) })
}

/** Send a guess. The response is the whole updated game, so it replaces the cached one. */
export function useGuessMutation(day: GameDay) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (guess: string) => sendGuess(day, guess),
    onSuccess: (game) => queryClient.setQueryData(gameKey(day), game),
  })
}

export function useWordHeartbeat(day: GameDay, active: MaybeRefOrGetter<boolean>) {
  useHeartbeat(() => sendHeartbeat(day), active)
}
