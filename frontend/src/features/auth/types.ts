// Types of the Auth (Google login, guest identity, route guards) feature.

export interface UserProfile {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  display_name: string
}

export interface SessionState {
  is_authenticated: boolean
  guest_id: string
  user: UserProfile | null
}
