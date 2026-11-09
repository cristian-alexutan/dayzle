// useBoardState: what a tap does, and undoing the player's changes.
import { computed, ref, toValue, type MaybeRefOrGetter } from 'vue'

import { contentOf, sameCell } from '../board'
import type { Cell, CellChange, CellContent, LogicGame } from '../types'

/** Each tap moves a cell one step: empty → X → sun → empty. */
const NEXT: Record<CellContent, CellContent> = { empty: 'mark', mark: 'sun', sun: 'empty' }

interface BoardStateOptions {
  game: MaybeRefOrGetter<LogicGame | undefined>
  /** No taps once the game is over. */
  disabled: MaybeRefOrGetter<boolean>
  change: (change: CellChange) => void
}

/**
 * The board itself comes from the server (see `useCellMutation`); this keeps what is needed to
 * undo: each change remembers what the cell held before it.
 */
export function useBoardState(options: BoardStateOptions) {
  const history = ref<CellChange[]>([])

  const contentAt = (cell: Cell) => contentOf(toValue(options.game), cell)

  function tap(cell: Cell) {
    if (toValue(options.disabled)) return
    const before = contentAt(cell)
    history.value.push({ cell, content: before })
    options.change({ cell, content: NEXT[before] })
  }

  /** Put the cell of the last change back as it was. */
  function undo() {
    if (toValue(options.disabled)) return
    const last = history.value.pop()
    if (last) options.change(last)
  }

  /** A rejected sun never reached the board, so there is nothing to undo for it. */
  function forget(cell: Cell) {
    for (let index = history.value.length - 1; index >= 0; index--) {
      if (sameCell(history.value[index]!.cell, cell)) {
        history.value.splice(index, 1)
        return
      }
    }
  }

  function clearHistory() {
    history.value = []
  }

  const canUndo = computed(() => history.value.length > 0)
  const isEmpty = computed(() => {
    const game = toValue(options.game)
    return !game || (game.suns.length === 0 && game.marks.length === 0)
  })

  return { contentOf: contentAt, tap, undo, forget, clearHistory, canUndo, isEmpty }
}
