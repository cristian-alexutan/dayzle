<!-- LogicBoard: the colored N × N grid. Thick lines separate the regions. -->
<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { Cell, CellContent } from '../types'
import LogicCell from './LogicCell.vue'

const props = defineProps<{
  regions: number[][]
  contentOf: (cell: Cell) => CellContent
  isWrong: (cell: Cell) => boolean
  isConflict: (cell: Cell) => boolean
  disabled?: boolean
}>()

defineEmits<{ tap: [cell: Cell] }>()

const { t } = useI18n()

const size = computed(() => props.regions.length)

const cells = computed(() =>
  props.regions.flatMap((row, r) =>
    row.map((region, c) => ({
      cell: [r, c] as Cell,
      region,
      edges: {
        top: r === 0 || props.regions[r - 1]![c] !== region,
        right: c === row.length - 1 || row[c + 1] !== region,
        bottom: r === props.regions.length - 1 || props.regions[r + 1]![c] !== region,
        left: c === 0 || row[c - 1] !== region,
      },
    })),
  ),
)

function label([row, col]: Cell) {
  const content = props.contentOf([row, col])
  return t(`logic.cell.${content}`, { row: row + 1, col: col + 1 })
}
</script>

<template>
  <div
    class="logic-board"
    role="grid"
    :aria-label="t('logic.board')"
    :style="{ gridTemplateColumns: `repeat(${size}, 1fr)` }"
  >
    <LogicCell
      v-for="{ cell, region, edges } in cells"
      :key="`${cell[0]}-${cell[1]}`"
      :region="region"
      :edges="edges"
      :content="contentOf(cell)"
      :wrong="isWrong(cell)"
      :conflict="isConflict(cell)"
      :label="label(cell)"
      :disabled="disabled"
      @tap="$emit('tap', cell)"
    />
  </div>
</template>

<style scoped>
.logic-board {
  display: grid;
  width: min(100%, 26rem);
  border: 2px solid var(--dz-region-edge);
  border-radius: 0.4rem;
  overflow: hidden;
}
</style>
