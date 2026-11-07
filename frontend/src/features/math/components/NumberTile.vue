<!-- NumberTile: one number on the board. Computed numbers have a "new" badge. -->
<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import AppButton from '@/shared/components/AppButton.vue'

import type { Tile } from '../composables/useMathBoard'

const props = defineProps<{
  tile: Tile
  selected?: boolean
  refused?: boolean
  /** Plays the shake once; the parent turns it off again, so a second refusal shakes too. */
  shaking?: boolean
  disabled?: boolean
}>()
defineEmits<{ select: [] }>()

const { t } = useI18n()

const label = computed(() =>
  [
    props.tile.value,
    props.tile.computed && t('math.tile.computed'),
    props.selected && t('math.tile.selected'),
    props.refused && t('math.tile.refused'),
  ]
    .filter(Boolean)
    .join(', '),
)
</script>

<template>
  <AppButton
    class="number-tile"
    :class="{
      'number-tile--computed': tile.computed,
      'number-tile--selected': selected,
      'number-tile--refused': refused,
      'number-tile--shaking': shaking,
    }"
    severity="secondary"
    :aria-label="label"
    :aria-pressed="selected ? 'true' : 'false'"
    :disabled="disabled"
    data-test="tile"
    @click="$emit('select')"
  >
    <i v-if="selected" class="number-tile__mark pi pi-check" aria-hidden="true" />
    <i v-else-if="refused" class="number-tile__mark pi pi-times-circle" aria-hidden="true" />
    <span v-if="tile.computed" class="number-tile__badge" aria-hidden="true">
      {{ t('math.tile.new') }}
    </span>
    <span>{{ tile.value }}</span>
  </AppButton>
</template>

<style scoped>
.number-tile {
  --tile-background: var(--dz-surface);
  --tile-color: var(--dz-text);
  --tile-border: var(--dz-border);
  --p-button-secondary-background: var(--tile-background);
  --p-button-secondary-hover-background: var(--tile-background);
  --p-button-secondary-active-background: var(--tile-background);
  --p-button-secondary-border-color: var(--tile-border);
  --p-button-secondary-hover-border-color: var(--tile-border);
  --p-button-secondary-active-border-color: var(--tile-border);
  --p-button-secondary-color: var(--tile-color);
  --p-button-secondary-hover-color: var(--tile-color);
  --p-button-secondary-active-color: var(--tile-color);
  position: relative;
  height: 4.25rem;
  border-width: 2px;
  border-radius: 1.125rem;
  font-size: 1.75rem;
  font-weight: 800;
  transition: transform 0.15s;
}

.number-tile--computed {
  --tile-background: var(--dz-primary);
  --tile-color: var(--dz-on-primary);
  --tile-border: var(--dz-primary-strong);
  border-style: dashed;
}

.number-tile--selected {
  --tile-background: var(--dz-primary-strong);
  --tile-color: var(--dz-on-primary-strong);
  --tile-border: var(--dz-primary-strong);
  border-style: solid;
  box-shadow:
    0 0 0 3px var(--dz-page),
    0 0 0 6px var(--dz-primary-strong);
  transform: translateY(-3px);
}

.number-tile--refused {
  --tile-color: var(--dz-accent-strong);
  --tile-border: var(--dz-accent-strong);
}

.number-tile--shaking {
  animation: number-tile-shake 0.4s;
}

.number-tile__mark {
  position: absolute;
  top: 0.4rem;
  left: 0.5rem;
  font-size: 0.85rem;
}

.number-tile__badge {
  position: absolute;
  top: 0.4rem;
  right: 0.5rem;
  padding: 0 0.375rem;
  border-radius: 999px;
  background: var(--dz-primary-strong);
  color: var(--dz-on-primary-strong);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.number-tile--selected .number-tile__badge {
  border: 1px solid currentColor;
  background: transparent;
  color: inherit;
}

@keyframes number-tile-shake {
  25% {
    transform: translateX(-6px) rotate(-2deg);
  }
  75% {
    transform: translateX(6px) rotate(2deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .number-tile {
    transition: none;
  }

  .number-tile--shaking {
    animation: none;
  }
}
</style>
