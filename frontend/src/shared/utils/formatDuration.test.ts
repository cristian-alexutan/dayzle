import { describe, expect, it } from 'vitest'

import { formatDuration } from './formatDuration'

describe('formatDuration', () => {
  it.each([
    [0, '0:00'],
    [5_999, '0:05'],
    [65_000, '1:05'],
    [3_723_000, '1:02:03'],
  ])('formats %d ms as %s', (ms, expected) => {
    expect(formatDuration(ms)).toBe(expected)
  })
})
