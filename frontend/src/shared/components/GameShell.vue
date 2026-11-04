<!-- GameShell: Common frame around every game: its title in colored tiles and a content column. -->
<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ title: string }>()

const letters = computed(() => Array.from(props.title))
</script>

<template>
  <main class="game-shell">
    <h1 class="game-shell__title" :aria-label="title">
      <span
        v-for="(letter, index) in letters"
        :key="index"
        class="game-shell__letter"
        aria-hidden="true"
        >{{ letter }}</span
      >
    </h1>
    <slot />
  </main>
</template>

<style scoped>
.game-shell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  max-width: 32rem;
  margin: 0 auto;
  padding: 0 1rem 1rem;
}

.game-shell__title {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.2rem;
  margin: 0;
}

.game-shell__letter {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.9rem;
  height: 1.9rem;
  border-radius: 0.35rem;
  background: var(--dz-correct);
  color: var(--dz-on-correct);
  font-size: 1.1rem;
  font-weight: 800;
  text-transform: uppercase;
}

.game-shell__letter:nth-child(3n + 2) {
  background: var(--dz-accent);
  color: var(--dz-on-accent);
}

.game-shell__letter:nth-child(3n) {
  background: var(--dz-present);
  color: var(--dz-on-present);
}
</style>
