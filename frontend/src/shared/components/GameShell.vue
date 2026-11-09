<!-- GameShell: Common frame around every game: its title and a centered content column. -->
<script setup lang="ts">
/** `wide` gives games built around a large picture (the GeoGuesser) more room. */
defineProps<{ title: string; wide?: boolean }>()
</script>

<template>
  <main class="game-shell" :class="{ 'game-shell--wide': wide }">
    <h1 class="game-shell__title">{{ title }}</h1>
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

.game-shell--wide {
  max-width: 60rem;
}

.game-shell__title {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 800;
  letter-spacing: 0.02em;
}
</style>
