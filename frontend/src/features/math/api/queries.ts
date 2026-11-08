// TanStack Query hooks for the Math feature.
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import type { MaybeRefOrGetter } from 'vue'

import { ApiError } from '@/api/http'
import { useHeartbeat } from '@/shared/composables/useHeartbeat'

import type { GameDay, MathGame, StepInput } from '../types'
import { fetchGame, saveProgress, sendHeartbeat, submitGame } from './endpoints'

const gameKey = (day: GameDay) => ['math', 'game', day]

/** The backend's error code (`no_puzzle`, `invalid_step`, ...), or null for any other error. */
export function errorCode(error: unknown): string | null {
  return error instanceof ApiError ? error.code : null
}

export function useMathGameQuery(day: GameDay) {
  return useQuery({ queryKey: gameKey(day), queryFn: () => fetchGame(day) })
}

/**
 * Every response is the whole updated board, so it replaces the cached one. A reload already on
 * its way is cancelled first: it started before this change, so its answer would bring back
 * the older board after this one is saved.
 */
function useBoardMutation(
  day: GameDay,
  send: (day: GameDay, steps: StepInput[]) => Promise<MathGame>,
) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (steps: StepInput[]) => send(day, steps),
    onMutate: () => queryClient.cancelQueries({ queryKey: gameKey(day) }),
    onSuccess: (game) => queryClient.setQueryData(gameKey(day), game),
  })
}

/**
 * Save the board after a step, undo or reset. A step that reaches the target finishes the
 * game: the response then has `status: 'completed'`, with the score and the solution.
 */
export function useSaveProgressMutation(day: GameDay) {
  return useBoardMutation(day, saveProgress)
}

/** Finish the game with the closest number so far. */
export function useSubmitMutation(day: GameDay) {
  return useBoardMutation(day, submitGame)
}

/** Count thinking time as active: a heartbeat every 15 s while `active` and the page is visible. */
export function useMathHeartbeat(day: GameDay, active: MaybeRefOrGetter<boolean>) {
  useHeartbeat(() => sendHeartbeat(day), active)
}
