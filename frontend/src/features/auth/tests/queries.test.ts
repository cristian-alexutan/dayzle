import { useQueryClient, type QueryClient } from '@tanstack/vue-query'
import { flushPromises } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { defineComponent } from 'vue'

import { mountWithPlugins } from '@/tests/utils'

import {
  sessionKey,
  useGoogleLoginMutation,
  useLogoutMutation,
  useSessionQuery,
} from '../api/queries'
import { createGuestOnlyGuard, createRequireAuthGuard } from '../guards'
import type { SessionState } from '../types'

function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const GUEST_SESSION: SessionState = {
  is_authenticated: false,
  guest_id: '11111111-1111-1111-1111-111111111111',
  user: null,
}

const USER_SESSION: SessionState = {
  is_authenticated: true,
  guest_id: '11111111-1111-1111-1111-111111111111',
  user: {
    id: 1,
    username: 'andrei',
    email: 'andrei@example.com',
    first_name: 'Andrei',
    last_name: 'Maxim',
    display_name: 'Andrei Maxim',
  },
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('auth queries and route guards', () => {
  it('loads the current session and updates cached state on login and logout', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(200, GUEST_SESSION))
      .mockResolvedValueOnce(jsonResponse(200, USER_SESSION))
      .mockResolvedValueOnce(jsonResponse(200, GUEST_SESSION))
    vi.stubGlobal('fetch', fetchMock)

    let state: ReturnType<typeof useSessionQuery> | undefined
    let login: ReturnType<typeof useGoogleLoginMutation> | undefined
    let logout: ReturnType<typeof useLogoutMutation> | undefined

    const Harness = defineComponent({
      setup() {
        state = useSessionQuery()
        login = useGoogleLoginMutation()
        logout = useLogoutMutation()
        return () => null
      },
    })

    const wrapper = mountWithPlugins(Harness)
    await flushPromises()

    expect(state?.data.value).toEqual(GUEST_SESSION)

    login?.mutate('google-jwt-token')
    await flushPromises()
    expect(state?.data.value).toEqual(USER_SESSION)

    logout?.mutate()
    await flushPromises()
    expect(state?.data.value).toEqual(GUEST_SESSION)
    expect(sessionKey).toEqual(['auth', 'session'])
    wrapper.unmount()
  })

  it.each([
    ['signing in', (login: () => void) => login],
    ['signing out', (_login: () => void, logout: () => void) => logout],
  ])('drops the previous player’s cached games after %s', async (_name, pick) => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async () => jsonResponse(200, USER_SESSION)),
    )
    let queryClient: QueryClient | undefined
    let login: ReturnType<typeof useGoogleLoginMutation> | undefined
    let logout: ReturnType<typeof useLogoutMutation> | undefined

    const Harness = defineComponent({
      setup() {
        queryClient = useQueryClient()
        login = useGoogleLoginMutation()
        logout = useLogoutMutation()
        return () => null
      },
    })
    const wrapper = mountWithPlugins(Harness)
    const gameKey = ['geo', 'game', 'today', 'default']
    queryClient!.setQueryData(gameKey, { status: 'completed' })

    pick(
      () => login!.mutate('google-jwt-token'),
      () => logout!.mutate(),
    )()
    await flushPromises()

    expect(queryClient!.getQueryData(gameKey)).toBeUndefined()
    expect(queryClient!.getQueryData(sessionKey)).toEqual(USER_SESSION)
    wrapper.unmount()
  })

  it('evaluates guest-only and require-auth guards', () => {
    const guestGuardForGuest = createGuestOnlyGuard(() => GUEST_SESSION)
    const guestGuardForUser = createGuestOnlyGuard(() => USER_SESSION)

    expect(guestGuardForGuest({ fullPath: '/login' } as never)).toBe(true)
    expect(guestGuardForUser({ fullPath: '/login' } as never)).toEqual({ path: '/' })

    const requireAuthForGuest = createRequireAuthGuard(() => GUEST_SESSION)
    const requireAuthForUser = createRequireAuthGuard(() => USER_SESSION)

    expect(requireAuthForGuest({ fullPath: '/stats' } as never)).toEqual({
      path: '/login',
      query: { next: '/stats' },
    })
    expect(requireAuthForUser({ fullPath: '/stats' } as never)).toBe(true)
  })
})
