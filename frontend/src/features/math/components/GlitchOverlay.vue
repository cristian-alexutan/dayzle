<!-- GlitchOverlay: the 404 easter egg, scan lines over the board and "404 · Number not found". -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import { EGG_MS } from '../composables/useEasterEggs'

const { t } = useI18n()
</script>

<template>
  <div class="glitch-overlay" :style="{ '--egg-ms': `${EGG_MS}ms` }" aria-hidden="true">
    <span class="glitch-overlay__label" data-test="glitch-label">{{
      t('math.eggs.notFound')
    }}</span>
  </div>
</template>

<style scoped>
.glitch-overlay {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  border-radius: 1.375rem;
  background: repeating-linear-gradient(
    0deg,
    color-mix(in srgb, var(--dz-text) 12%, transparent) 0 2px,
    transparent 2px 5px
  );
  pointer-events: none;
  animation: glitch-overlay-flicker var(--egg-ms) steps(1, end) both;
}

.glitch-overlay__label {
  padding: 0.75rem 1.125rem;
  border: 2px solid var(--dz-text);
  border-radius: 0.75rem;
  background: var(--dz-surface);
  color: var(--dz-text);
  font-family: ui-monospace, monospace;
  font-size: 1.0625rem;
  font-weight: 700;
  text-shadow:
    -2px 0 var(--dz-accent),
    2px 0 var(--dz-primary);
  animation: glitch-overlay-split calc(var(--egg-ms) / 8) steps(2, end) infinite;
}

@keyframes glitch-overlay-flicker {
  0% {
    opacity: 0;
  }
  6%,
  92% {
    opacity: 1;
  }
  48% {
    opacity: 0.6;
  }
  52% {
    opacity: 1;
  }
  100% {
    opacity: 0;
  }
}

@keyframes glitch-overlay-split {
  from {
    transform: translateX(-2px);
  }
  to {
    transform: translateX(2px);
  }
}

@media (prefers-reduced-motion: reduce) {
  .glitch-overlay,
  .glitch-overlay__label {
    animation: none;
  }
}
</style>
