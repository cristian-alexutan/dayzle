<!-- GameShell: Common frame around every game: its title, actions and a centered column. -->
<script setup lang="ts">
/**
 * `wide` gives games built around a large picture (the GeoGuesser) more room. The `title` slot
 * replaces how the title is drawn (a logo-like title); `title` stays its text. The `actions`
 * slot puts buttons (such as a hint) at the top right, next to the centered title.
 */
defineProps<{ title: string; wide?: boolean }>()
</script>

<template>
  <main class="game-shell" :class="{ 'game-shell--wide': wide }">
    <header class="game-shell__header">
      <h1 class="game-shell__title">
        <slot name="title">{{ title }}</slot>
      </h1>
      <div v-if="$slots.actions" class="game-shell__actions">
        <slot name="actions" />
      </div>
    </header>
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

/* Three columns keep the title centered whatever the actions on its right take. */
.game-shell__header {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
}

.game-shell__title {
  grid-column: 2;
  margin: 0;
  font-size: 1.75rem;
  font-weight: 800;
  letter-spacing: 0.02em;
  text-align: center;
}

.game-shell__actions {
  display: flex;
  grid-column: 3;
  justify-content: flex-end;
  gap: 0.5rem;
}
</style>
