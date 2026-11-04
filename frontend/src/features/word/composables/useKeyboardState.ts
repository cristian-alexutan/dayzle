// useKeyboardState: the best color each letter has reached (green over yellow over gray).
import { computed, toValue, type MaybeRefOrGetter } from 'vue'

import type { Guess, LetterColor } from '../types'

const RANK: Record<LetterColor, number> = { absent: 0, present: 1, correct: 2 }

export function useKeyboardState(guesses: MaybeRefOrGetter<Guess[]>) {
  return computed(() => {
    const best: Record<string, LetterColor> = {}
    for (const { word, colors } of toValue(guesses)) {
      Array.from(word).forEach((letter, index) => {
        const color = colors[index]!
        const current = best[letter]
        if (current === undefined || RANK[color] > RANK[current]) best[letter] = color
      })
    }
    return best
  })
}
