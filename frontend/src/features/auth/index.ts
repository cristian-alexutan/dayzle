// Public entry of the Auth (Google login, guest identity, route guards) feature: the only file other code may import from.
export {
  authErrorCode,
  sessionKey,
  useGoogleLoginMutation,
  useLogoutMutation,
  useSessionQuery,
} from './api/queries'
export { createGuestOnlyGuard, createRequireAuthGuard } from './guards'
export { authRoutes } from './routes'
export type { SessionState, UserProfile } from './types'
