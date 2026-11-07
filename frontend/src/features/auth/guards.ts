// Route guards (guest, user, subscriber, admin). UX only: the backend enforces access.
import type { RouteLocationNormalized, RouteLocationRaw } from 'vue-router'

import type { SessionState } from './types'

export type SessionReader = () => SessionState | undefined
export type AuthGuard = (to: RouteLocationNormalized) => boolean | RouteLocationRaw

/** Redirects signed-in users away from guest-only pages (such as /login) back to Home. */
export function createGuestOnlyGuard(getSession: SessionReader): AuthGuard {
  return () => {
    const session = getSession()
    if (session?.is_authenticated) {
      return { path: '/' }
    }
    return true
  }
}

/** Redirects anonymous guests to /login when visiting a route that requires a user account. */
export function createRequireAuthGuard(getSession: SessionReader): AuthGuard {
  return (to: RouteLocationNormalized) => {
    const session = getSession()
    if (!session?.is_authenticated) {
      return { path: '/login', query: { next: to.fullPath } }
    }
    return true
  }
}
