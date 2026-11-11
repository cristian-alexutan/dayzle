// TanStack Query hooks for the Trivia feature.
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import type { MaybeRefOrGetter } from 'vue'

import { useHeartbeat } from '@/shared/composables/useHeartbeat'

import type { GameDay } from '../types'
import { fetchGame, sendAnswer, sendHeartbeat } from './endpoints'

const gameKey = (day: GameDay) => ['trivia', 'game', day]

export { errorCode } from '@/api/http'

export function useTriviaGameQuery(day: GameDay) {
  return useQuery({ queryKey: gameKey(day), queryFn: () => fetchGame(day) })
}

/** Answer a question. The response is the whole updated quiz, so it replaces the cached one. */
export function useAnswerMutation(day: GameDay) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ question, choice }: { question: number; choice: number }) =>
      sendAnswer(day, question, choice),
    onSuccess: (game) => queryClient.setQueryData(gameKey(day), game),
  })
}

export function useTriviaHeartbeat(day: GameDay, active: MaybeRefOrGetter<boolean>) {
  useHeartbeat(() => sendHeartbeat(day), active)
}
