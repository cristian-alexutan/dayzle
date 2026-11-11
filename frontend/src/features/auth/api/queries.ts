// TanStack Query hooks for the Auth (Google login, guest identity, route guards) feature.
import { useMutation, useQuery, useQueryClient, type QueryClient } from '@tanstack/vue-query'

import { ApiError } from '@/api/http'

import type { SessionState } from '../types'
import { fetchSession, loginWithGoogle, logoutSession } from './endpoints'

export const sessionKey = ['auth', 'session'] as const

/** The backend's error code (`invalid_google_token`, ...), or null for any other error. */
export function authErrorCode(error: unknown): string | null {
  return error instanceof ApiError ? error.code : null
}

/**
 * After signing in or out the player is someone else (the account, or a new guest), so every
 * cached game is dropped and loaded again for them: nothing from the previous player is shown.
 */
function switchPlayer(queryClient: QueryClient, session: SessionState) {
  queryClient.setQueryData(sessionKey, session)
  return queryClient.resetQueries({ predicate: (query) => query.queryKey[0] !== sessionKey[0] })
}

export function useSessionQuery() {
  return useQuery({
    queryKey: sessionKey,
    queryFn: fetchSession,
  })
}

export function useGoogleLoginMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (credential: string) => loginWithGoogle(credential),
    onSuccess: (session) => switchPlayer(queryClient, session),
  })
}

export function useLogoutMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => logoutSession(),
    onSuccess: (session) => switchPlayer(queryClient, session),
  })
}
