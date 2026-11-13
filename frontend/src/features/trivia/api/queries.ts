// TanStack Query hooks for the Trivia feature.
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, toValue, type MaybeRefOrGetter } from 'vue'

import { useHeartbeat } from '@/shared/composables/useHeartbeat'

import type { GameDay } from '../types'
import { fetchGame, sendAnswer, sendHeartbeat } from './endpoints'

const gameKey = (day: GameDay) => ['trivia', 'game', day]

export { errorCode } from '@/api/http'

/** `enabled` holds the first load back: opening the quiz starts its clock. */
export function useTriviaGameQuery(day: GameDay, enabled: MaybeRefOrGetter<boolean> = true) {
  return useQuery({
    queryKey: gameKey(day),
    queryFn: () => fetchGame(day),
    enabled: computed(() => toValue(enabled)),
  })
}

/**
 * Answer a question. The response is the whole updated quiz, so it replaces the cached one. A
 * reload already on its way is cancelled first: it started before this answer, so its response
 * would bring back the quiz without it. One that starts while the answer is on its way is
 * cancelled too, before the answer is saved.
 */
export function useAnswerMutation(day: GameDay) {
  const queryClient = useQueryClient()
  const cancelReloads = () => queryClient.cancelQueries({ queryKey: gameKey(day) })
  return useMutation({
    mutationFn: ({ question, choice }: { question: number; choice: number }) =>
      sendAnswer(day, question, choice),
    onMutate: cancelReloads,
    onSuccess: async (game) => {
      await cancelReloads()
      queryClient.setQueryData(gameKey(day), game)
    },
  })
}

export function useTriviaHeartbeat(day: GameDay, active: MaybeRefOrGetter<boolean>) {
  useHeartbeat(() => sendHeartbeat(day), active)
}
