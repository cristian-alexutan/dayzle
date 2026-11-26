<!--
  GameActionButton: a button in a game's top row (hint, rules...). It looks like a key of the
  on-screen keyboard, so it belongs to the game, and turns green on hover. Attributes and
  events (click, title, data-test...) pass straight through.
-->
<script setup lang="ts">
import AppButton from './AppButton.vue'

defineProps<{ icon: string; label?: string; loading?: boolean; disabled?: boolean }>()
</script>

<template>
  <AppButton
    class="game-action"
    :class="{ 'game-action--icon-only': !label }"
    :icon="icon"
    :label="label"
    :loading="loading"
    :disabled="disabled"
    severity="secondary"
    @mousedown.prevent
  />
</template>

<style scoped>
.game-action {
  --p-button-secondary-background: var(--dz-key);
  --p-button-secondary-border-color: var(--dz-key);
  --p-button-secondary-color: var(--dz-on-key);
  --p-button-secondary-hover-background: var(--dz-primary);
  --p-button-secondary-hover-border-color: var(--dz-primary);
  --p-button-secondary-hover-color: var(--dz-on-primary);
  --p-button-secondary-active-background: var(--dz-primary-active);
  --p-button-secondary-active-border-color: var(--dz-primary-active);
  --p-button-secondary-active-color: var(--dz-on-primary);
  height: 2.25rem;
  padding-inline: 0.8rem;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  font-weight: 600;
  gap: 0.4rem;
}

.game-action--icon-only {
  width: 2.25rem;
  padding: 0;
}
</style>
