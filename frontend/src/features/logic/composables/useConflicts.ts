// useConflicts: briefly shows a wrong sun and the suns it breaks a rule with.
import { onScopeDispose, ref } from 'vue'

import type { Cell } from '../types'

/** How long a wrong sun stays on screen before it disappears. */
export const WRONG_SUN_MS = 900

const sameCell = (a: Cell, b: Cell) => a[0] === b[0] && a[1] === b[1]

export function useConflicts() {
  const wrongCell = ref<Cell | null>(null)
  const conflicts = ref<Cell[]>([])
  let timer: ReturnType<typeof setTimeout> | undefined

  function clear() {
    clearTimeout(timer)
    wrongCell.value = null
    conflicts.value = []
  }

  /** Show a wrong sun on `cell`, and highlight the suns the server says it conflicts with. */
  function show(cell: Cell, conflicting: Cell[]) {
    clear()
    wrongCell.value = cell
    conflicts.value = conflicting
    timer = setTimeout(clear, WRONG_SUN_MS)
  }

  const isWrong = (cell: Cell) => wrongCell.value !== null && sameCell(wrongCell.value, cell)
  const isConflict = (cell: Cell) => conflicts.value.some((other) => sameCell(other, cell))

  onScopeDispose(clear)

  return { show, clear, isWrong, isConflict }
}
