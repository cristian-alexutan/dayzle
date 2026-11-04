<!-- WordBoard: the rows of tiles. Tiles flip to reveal their colors; a rejected guess shakes. -->
<script setup lang="ts">
import { computed } from 'vue'

import type { Guess, LetterColor } from '../types'

const props = defineProps<{
  guesses: Guess[]
  current: string[]
  rows: number
  length: number
  /** The row that flips once it holds a guess. Rows restored from the server don't flip. */
  revealRow?: number | null
  shake?: boolean
}>()

const isRevealing = (rowIndex: number) =>
  rowIndex === props.revealRow && rowIndex < props.guesses.length

interface Tile {
  letter: string
  color: LetterColor | null
}

const board = computed<Tile[][]>(() =>
  Array.from({ length: props.rows }, (_row, rowIndex) => {
    const guess = props.guesses[rowIndex]
    const letters = guess
      ? Array.from(guess.word)
      : rowIndex === props.guesses.length
        ? props.current
        : []
    return Array.from({ length: props.length }, (_tile, index) => ({
      letter: letters[index] ?? '',
      color: guess?.colors[index] ?? null,
    }))
  }),
)
</script>

<template>
  <div class="word-board" role="grid">
    <div
      v-for="(row, rowIndex) in board"
      :key="rowIndex"
      class="word-board__row"
      :class="{ 'word-board__row--shake': shake && rowIndex === guesses.length }"
      role="row"
      data-test="row"
    >
      <div
        v-for="(tile, index) in row"
        :key="index"
        class="word-board__tile"
        :class="[
          tile.color && `word-board__tile--${tile.color}`,
          tile.letter && !tile.color && 'word-board__tile--filled',
          isRevealing(rowIndex) && 'word-board__tile--reveal',
        ]"
        :style="isRevealing(rowIndex) ? { animationDelay: `${index * 250}ms` } : undefined"
        role="gridcell"
        data-test="tile"
      >
        {{ tile.letter }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.word-board {
  display: grid;
  gap: 0.35rem;
  width: min(100%, 20rem);
}

.word-board__row {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: 1fr;
  gap: 0.35rem;
}

.word-board__tile {
  display: flex;
  align-items: center;
  justify-content: center;
  aspect-ratio: 1;
  border: 2px solid var(--word-border);
  background: var(--tile-background, transparent);
  color: var(--tile-color, var(--p-text-color));
  font-size: 1.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.word-board__tile--filled {
  border-color: var(--word-border-filled);
}

.word-board__tile--correct,
.word-board__tile--present,
.word-board__tile--absent {
  --tile-color: var(--word-on-color);
  border-color: var(--tile-background);
}

.word-board__tile--correct {
  --tile-background: var(--word-correct);
}

.word-board__tile--present {
  --tile-background: var(--word-present);
}

.word-board__tile--absent {
  --tile-background: var(--word-absent);
}

.word-board__tile--reveal {
  animation: word-flip 500ms ease-in-out backwards;
}

.word-board__row--shake {
  animation: word-shake 400ms ease-in-out;
}

/* Until the tile is edge-on it still looks unguessed; then it shows its color. */
@keyframes word-flip {
  0% {
    transform: rotateX(0);
    border-color: var(--word-border-filled);
    background: transparent;
    color: var(--p-text-color);
  }
  49% {
    border-color: var(--word-border-filled);
    background: transparent;
    color: var(--p-text-color);
  }
  50% {
    transform: rotateX(90deg);
    border-color: var(--tile-background);
    background: var(--tile-background);
    color: var(--tile-color);
  }
  100% {
    transform: rotateX(0);
  }
}

@keyframes word-shake {
  20%,
  60% {
    transform: translateX(-0.4rem);
  }
  40%,
  80% {
    transform: translateX(0.4rem);
  }
}

@media (prefers-reduced-motion: reduce) {
  .word-board__tile--reveal,
  .word-board__row--shake {
    animation: none;
  }
}
</style>
