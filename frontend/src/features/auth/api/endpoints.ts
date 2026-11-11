// Thin wrappers over the generated API client for the Auth (Google login, guest identity, route guards) feature.
import { http } from '@/api/http'

import type { SessionState } from '../types'

export function fetchSession() {
  return http.get<SessionState>('/accounts/me/')
}

export function loginWithGoogle(credential: string) {
  return http.post<SessionState>('/accounts/google/', { credential })
}

export function logoutSession() {
  return http.post<SessionState>('/accounts/logout/')
}
