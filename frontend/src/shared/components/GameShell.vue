<!-- GameShell: Common frame around every game: its title and a centered content column. -->
<script setup lang="ts">
defineProps<{ title: string }>()
</script>

<template>
  <main class="game-shell">
    <h1 class="game-shell__title">{{ title }}</h1>
    <slot />
  </main>
</template>

<style scoped>
.game-shell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  max-width: 32rem;
  margin: 0 auto;
  padding: 0 1rem 1rem;
}

.game-shell__title {
  margin: 0;
  font-size: 1.75rem;
}
</style>
