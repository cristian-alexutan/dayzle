/**
 * A puzzle's day in the player's language: "sâmbătă, 7 noiembrie" for `2026-11-07` in `ro`.
 * The date is read as a calendar day, so the time zone can't move it to the day before.
 */
export function formatGameDay(isoDate: string, locale: string): string {
  const [year, month, day] = isoDate.split('-').map(Number) as [number, number, number]
  return new Intl.DateTimeFormat(locale, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  }).format(new Date(year, month - 1, day))
}
