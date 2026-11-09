// useConflicts: briefly shows a rejected sun and the suns it breaks a rule with.
import { onScopeDispose, ref } from 'vue'

import { sameCell } from '../board'
import type { Cell } from '../types'

/** How long a rejected sun stays on screen before it disappears. */
export const REJECTED_SUN_MS = 900

export function useConflicts() {
  const rejectedCell = ref<Cell | null>(null)
  const conflicts = ref<Cell[]>([])
  let timer: ReturnType<typeof setTimeout> | undefined

  function clear() {
    clearTimeout(timer)
    rejectedCell.value = null
    conflicts.value = []
  }

  /** Show a rejected sun on `cell`, and highlight the suns the server says it conflicts with. */
  function show(cell: Cell, conflicting: Cell[]) {
    clear()
    rejectedCell.value = cell
    conflicts.value = conflicting
    timer = setTimeout(clear, REJECTED_SUN_MS)
  }

  const isRejected = (cell: Cell) =>
    rejectedCell.value !== null && sameCell(rejectedCell.value, cell)
  const isConflict = (cell: Cell) => conflicts.value.some((other) => sameCell(other, cell))

  onScopeDispose(clear)

  return { show, clear, isRejected, isConflict }
}
