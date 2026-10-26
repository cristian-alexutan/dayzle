import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError, http } from './http'

const fetchMock = vi.fn()

function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  fetchMock.mockReset()
  vi.unstubAllGlobals()
  document.cookie = 'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT'
})

describe('http', () => {
  it('sends requests to the API base URL with the session cookie and returns the JSON body', async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, { ok: true }))

    await expect(http.get('/games/word/today/')).resolves.toEqual({ ok: true })

    const [url, init] = fetchMock.mock.calls[0]!
    expect(url).toBe('/api/v1/games/word/today/')
    expect(init).toMatchObject({ method: 'GET', credentials: 'same-origin' })
  })

  it('sends a JSON body and the CSRF token on unsafe methods', async () => {
    document.cookie = 'csrftoken=abc123'
    fetchMock.mockResolvedValue(jsonResponse(200, {}))

    await http.post('/games/word/today/guess/', { guess: 'PÂINE' })

    const [, init] = fetchMock.mock.calls[0]!
    expect(init.body).toBe(JSON.stringify({ guess: 'PÂINE' }))
    expect(init.headers).toMatchObject({
      'Content-Type': 'application/json',
      'X-CSRFToken': 'abc123',
    })
  })

  it('returns undefined for 204 No Content', async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }))

    await expect(http.delete('/something/')).resolves.toBeUndefined()
  })

  it('turns the backend error format into an ApiError', async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(409, {
        error: { code: 'already_played', message: 'Already played.', details: null },
      }),
    )

    const error = await http.post('/games/word/today/guess/').catch((e: unknown) => e)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 409, code: 'already_played', message: 'Already played.' })
  })

  it('turns other failed responses into a generic ApiError', async () => {
    fetchMock.mockResolvedValue(new Response('<h1>Server Error</h1>', { status: 500 }))

    const error = await http.get('/boom/').catch((e: unknown) => e)

    expect(error).toMatchObject({ status: 500, code: 'http_error' })
  })

  it('turns network failures into an ApiError with status 0', async () => {
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'))

    const error = await http.get('/games/word/today/').catch((e: unknown) => e)

    expect(error).toMatchObject({ status: 0, code: 'network_error' })
  })
})
