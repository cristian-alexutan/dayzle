// TanStack Query hooks for the Logic feature.
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, toValue, type MaybeRefOrGetter } from 'vue'

import { useHeartbeat } from '@/shared/composables/useHeartbeat'

import { withChange } from '../board'
import type { Cell, CellChange, GameDay, LogicGame } from '../types'
import { clearBoard, fetchGame, sendHeartbeat, setCell } from './endpoints'

export { errorCode } from '@/api/http'

const gameKey = (day: GameDay) => ['logic', 'game', day]
const boardKey = (day: GameDay) => ['logic', 'board', day]

/** The day's game. With `enabled` false it isn't fetched yet, so the clock doesn't start. */
export function useLogicGameQuery(day: GameDay, enabled: MaybeRefOrGetter<boolean> = true) {
  return useQuery({
    queryKey: gameKey(day),
    queryFn: () => fetchGame(day),
    enabled: computed(() => toValue(enabled)),
  })
}

interface BoardCallbacks {
  /** A new sun broke a rule: the server didn't keep it, and counted a mistake. */
  onRejected?: (cell: Cell, conflicts: Cell[]) => void
  onError?: (error: unknown) => void
}

/**
 * Changes to the board (cells and clearing) are sent one at a time, in the order the player
 * made them, and shown right away. Each response holds the whole board; it only replaces the
 * cached one when no newer change is still waiting, so the screen never goes back in time.
 */
function useBoardMutation<Variables, Result>(
  day: GameDay,
  send: (variables: Variables) => Promise<Result>,
  options: {
    optimistic: (game: LogicGame, variables: Variables) => LogicGame
    boardOf: (result: Result) => LogicGame
    onSuccess?: (result: Result, variables: Variables) => void
    onError?: (error: unknown) => void
  },
) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationKey: boardKey(day),
    scope: { id: `logic-board-${day}` },
    mutationFn: send,
    onMutate: async (variables: Variables) => {
      // A refetch that started earlier could finish later and bring back an older board.
      await queryClient.cancelQueries({ queryKey: gameKey(day) })
      const game = queryClient.getQueryData<LogicGame>(gameKey(day))
      if (game) queryClient.setQueryData(gameKey(day), options.optimistic(game, variables))
    },
    onSuccess: (result, variables) => {
      // This change is still counted as running, so 1 means no newer one is waiting.
      if (queryClient.isMutating({ mutationKey: boardKey(day) }) <= 1) {
        queryClient.setQueryData(gameKey(day), options.boardOf(result))
      }
      options.onSuccess?.(result, variables)
    },
    onError: (error) => {
      // The screen may show a change the server never made: load the real board again.
      queryClient.invalidateQueries({ queryKey: gameKey(day) })
      options.onError?.(error)
    },
  })
}

/** Set a cell to empty, an X or a sun. */
export function useCellMutation(day: GameDay, callbacks: BoardCallbacks = {}) {
  return useBoardMutation(day, (change: CellChange) => setCell(day, change), {
    optimistic: withChange,
    boardOf: (result) => result.game,
    onSuccess: (result, change) => {
      if (result.rejected) callbacks.onRejected?.(change.cell, result.conflicts)
    },
    onError: callbacks.onError,
  })
}

/** Remove every sun and X. Mistakes and time are kept. */
export function useClearMutation(day: GameDay, callbacks: BoardCallbacks = {}) {
  return useBoardMutation(day, () => clearBoard(day), {
    optimistic: (game) => ({ ...game, suns: [], marks: [] }),
    boardOf: (game) => game,
    onError: callbacks.onError,
  })
}

export function useLogicHeartbeat(day: GameDay, active: MaybeRefOrGetter<boolean>) {
  useHeartbeat(() => sendHeartbeat(day), active)
}
