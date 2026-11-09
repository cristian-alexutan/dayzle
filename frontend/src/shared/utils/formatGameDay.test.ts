import { describe, expect, it } from 'vitest'

import { formatGameDay } from './formatGameDay'

describe('formatGameDay', () => {
  it.each([
    ['ro', 'sâmbătă, 7 noiembrie'],
    ['en', 'Saturday, November 7'],
  ])('formats the day in %s as %s', (locale, expected) => {
    expect(formatGameDay('2026-11-07', locale)).toBe(expected)
  })

  it('keeps the first of the month on its own day', () => {
    expect(formatGameDay('2026-12-01', 'ro')).toBe('marți, 1 decembrie')
  })
})
