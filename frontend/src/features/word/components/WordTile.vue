<!-- WordTile: one letter box. Its color says how the letter did; `accent` reveals a missed word. -->
<script setup lang="ts">
import type { LetterColor } from '../types'

defineProps<{ letter: string; color?: LetterColor | 'accent' | null }>()
</script>

<template>
  <div
    class="word-tile"
    :class="[color && `word-tile--${color}`, letter && !color && 'word-tile--filled']"
  >
    {{ letter }}
  </div>
</template>

<style scoped>
.word-tile {
  display: flex;
  align-items: center;
  justify-content: center;
  aspect-ratio: 1;
  border: 2px solid var(--dz-border);
  border-radius: 0.4rem;
  background: var(--tile-background, transparent);
  color: var(--tile-color, var(--dz-text));
  font-size: 1.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.word-tile--filled {
  border-color: var(--dz-border-strong);
}

.word-tile--correct,
.word-tile--present,
.word-tile--absent,
.word-tile--accent {
  border-color: var(--tile-background);
}

.word-tile--correct {
  --tile-background: var(--dz-correct);
  --tile-color: var(--dz-on-correct);
}

.word-tile--present {
  --tile-background: var(--dz-present);
  --tile-color: var(--dz-on-present);
}

.word-tile--absent {
  --tile-background: var(--dz-absent);
  --tile-color: var(--dz-on-absent);
}

.word-tile--accent {
  --tile-background: var(--dz-accent);
  --tile-color: var(--dz-on-accent);
}
</style>
