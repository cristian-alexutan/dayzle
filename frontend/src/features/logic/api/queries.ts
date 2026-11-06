// TanStack Query hooks for the Logic feature.
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import type { MaybeRefOrGetter } from 'vue'

import { ApiError } from '@/api/http'
import { useHeartbeat } from '@/shared/composables/useHeartbeat'

import type { Cell, GameDay } from '../types'
import { fetchGame, placeSun, saveMarks, sendHeartbeat } from './endpoints'

const gameKey = (day: GameDay) => ['logic', 'game', day]

/** The backend's error code (`no_puzzle`, `already_played`, ...), or null for any other error. */
export function errorCode(error: unknown): string | null {
  return error instanceof ApiError ? error.code : null
}

export function useLogicGameQuery(day: GameDay) {
  return useQuery({ queryKey: gameKey(day), queryFn: () => fetchGame(day) })
}

/** Place a sun. The response holds the whole updated game, so it replaces the cached one. */
export function usePlaceMutation(day: GameDay) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (cell: Cell) => placeSun(day, cell),
    onSuccess: (result) => queryClient.setQueryData(gameKey(day), result.game),
  })
}

/**
 * Save the X marks. The board keeps its own marks while playing, so the response doesn't
 * replace the cached game: it could arrive after a newer sun and hide it.
 */
export function useMarksMutation(day: GameDay) {
  return useMutation({ mutationFn: (marks: Cell[]) => saveMarks(day, marks) })
}

export function useLogicHeartbeat(day: GameDay, active: MaybeRefOrGetter<boolean>) {
  useHeartbeat(() => sendHeartbeat(day), active)
}
