// useBoardState: what each cell shows, and what a tap does.
import { computed, onScopeDispose, ref, toValue, watch, type MaybeRefOrGetter } from 'vue'

import type { Cell, CellContent, LogicGame } from '../types'

/** Marks are saved a moment after the last tap, so quick taps send one request. */
export const MARKS_SAVE_DELAY_MS = 800

const key = ([row, col]: Cell) => `${row},${col}`
const cellOf = (value: string) => value.split(',').map(Number) as Cell

interface BoardStateOptions {
  game: MaybeRefOrGetter<LogicGame | undefined>
  /** No taps while a sun is being checked or once the game is over. */
  disabled: MaybeRefOrGetter<boolean>
  place: (cell: Cell) => void
  saveMarks: (marks: Cell[]) => void
}

/**
 * The first tap on an empty cell marks it with an X, and a tap on an X places a sun, which the
 * server checks. Suns come from the server; X marks live here while playing and are saved in the
 * background, so a refresh restores them.
 */
export function useBoardState(options: BoardStateOptions) {
  const marks = ref(new Set<string>())
  const suns = computed(() => new Set((toValue(options.game)?.suns ?? []).map(key)))

  // The server's marks are only read once: after that the board's own marks are newer.
  let marksLoaded = false
  watch(
    () => toValue(options.game),
    (game) => {
      if (!game || marksLoaded) return
      marks.value = new Set(game.marks.map(key))
      marksLoaded = true
    },
    { immediate: true },
  )

  let saveTimer: ReturnType<typeof setTimeout> | undefined

  function saveNow() {
    clearTimeout(saveTimer)
    saveTimer = undefined
    options.saveMarks([...marks.value].map(cellOf))
  }

  function scheduleSave() {
    clearTimeout(saveTimer)
    saveTimer = setTimeout(saveNow, MARKS_SAVE_DELAY_MS)
  }

  function contentOf(cell: Cell): CellContent {
    if (suns.value.has(key(cell))) return 'sun'
    if (marks.value.has(key(cell))) return 'mark'
    return 'empty'
  }

  function tap(cell: Cell) {
    if (toValue(options.disabled)) return
    const content = contentOf(cell)
    if (content === 'sun') return
    if (content === 'empty') {
      marks.value.add(key(cell))
      scheduleSave()
      return
    }
    // The server removes the X when a sun is placed, right or wrong, so do the same here.
    marks.value.delete(key(cell))
    options.place(cell)
  }

  // Leaving the page with an unsaved change: save it right away.
  onScopeDispose(() => {
    if (saveTimer !== undefined) saveNow()
  })

  return { contentOf, tap }
}
