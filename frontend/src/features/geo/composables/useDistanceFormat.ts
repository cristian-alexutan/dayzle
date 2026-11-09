// useDistanceFormat: distances in the player's language ("780 m", "1,2 km").
import { useI18n } from 'vue-i18n'

export function useDistanceFormat() {
  const { locale } = useI18n()

  return function formatDistance(meters: number) {
    const km = meters >= 1000
    return new Intl.NumberFormat(locale.value, {
      style: 'unit',
      unit: km ? 'kilometer' : 'meter',
      maximumFractionDigits: km ? 1 : 0,
    }).format(km ? meters / 1000 : meters)
  }
}
