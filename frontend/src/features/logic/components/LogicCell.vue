<!-- LogicCell: one cell of the grid, colored by its region. It can be empty, hold an X or a sun. -->
<script setup lang="ts">
import { computed } from 'vue'

import type { CellContent } from '../types'

/** Which sides of the cell border another region; those get a thick line. */
export interface RegionEdges {
  top: boolean
  right: boolean
  bottom: boolean
  left: boolean
}

const props = defineProps<{
  region: number
  content: CellContent
  edges: RegionEdges
  label: string
  /** A sun the server just rejected: shown in red for a moment, then removed. */
  wrong?: boolean
  /** A sun that the rejected one broke a rule with. */
  conflict?: boolean
  disabled?: boolean
}>()

defineEmits<{ tap: [] }>()

const regionColor = computed(() => ({ '--cell-background': `var(--dz-region-${props.region})` }))
</script>

<template>
  <button
    type="button"
    class="logic-cell"
    :class="{
      'logic-cell--wrong': wrong,
      'logic-cell--conflict': conflict,
      'logic-cell--edge-top': edges.top,
      'logic-cell--edge-right': edges.right,
      'logic-cell--edge-bottom': edges.bottom,
      'logic-cell--edge-left': edges.left,
    }"
    :style="regionColor"
    :aria-label="label"
    :disabled="disabled"
    data-test="cell"
    @click="$emit('tap')"
  >
    <i
      v-if="wrong || content === 'sun'"
      class="pi pi-sun logic-cell__sun"
      aria-hidden="true"
      data-test="sun"
    />
    <i v-else-if="content === 'mark'" class="pi pi-times logic-cell__mark" aria-hidden="true" />
  </button>
</template>

<style scoped>
.logic-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  aspect-ratio: 1;
  padding: 0;
  border: 1px solid var(--dz-region-line);
  background: var(--cell-background);
  color: var(--dz-on-region);
  cursor: pointer;
}

.logic-cell:disabled {
  cursor: default;
}

.logic-cell:focus-visible {
  outline: 3px solid var(--dz-primary-strong);
  outline-offset: -3px;
}

.logic-cell--edge-top {
  border-top: 2px solid var(--dz-region-edge);
}

.logic-cell--edge-right {
  border-right: 2px solid var(--dz-region-edge);
}

.logic-cell--edge-bottom {
  border-bottom: 2px solid var(--dz-region-edge);
}

.logic-cell--edge-left {
  border-left: 2px solid var(--dz-region-edge);
}

.logic-cell__sun {
  color: var(--dz-sun);
  font-size: 1.6rem;
}

.logic-cell__mark {
  font-size: 0.9rem;
  opacity: 0.7;
}

.logic-cell--wrong .logic-cell__sun {
  color: var(--dz-accent-strong);
  animation: logic-cell-shake 0.3s;
}

.logic-cell--conflict {
  box-shadow: inset 0 0 0 3px var(--dz-accent-strong);
}

@keyframes logic-cell-shake {
  25% {
    transform: translateX(-3px);
  }
  75% {
    transform: translateX(3px);
  }
}

@media (prefers-reduced-motion: reduce) {
  .logic-cell--wrong .logic-cell__sun {
    animation: none;
  }
}
</style>
