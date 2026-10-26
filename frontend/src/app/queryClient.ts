import { QueryClient } from '@tanstack/vue-query'

import { ApiError } from '@/api/http'

const MAX_RETRIES = 2

export function createAppQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Client errors (4xx) won't change on retry, so only retry network and server errors.
        retry: (failureCount, error) =>
          failureCount < MAX_RETRIES && !(error instanceof ApiError && error.status < 500),
      },
    },
  })
}
