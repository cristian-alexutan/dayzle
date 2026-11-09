<!-- FloatingPi: the 314 easter egg, a large π drifting across the board with "3.14" behind it. -->
<script setup lang="ts">
import { EGG_MS } from '../composables/useEasterEggs'
</script>

<template>
  <div class="floating-pi" :style="{ '--egg-ms': `${EGG_MS}ms` }" aria-hidden="true">
    <span class="floating-pi__symbol" data-test="pi">π</span>
    <span class="floating-pi__digits">3.14</span>
  </div>
</template>

<style scoped>
.floating-pi {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  color: var(--dz-accent);
}

.floating-pi__symbol {
  position: absolute;
  top: 50%;
  left: 50%;
  font-size: 9.5rem;
  font-weight: 900;
  line-height: 1;
  opacity: 0.75;
  transform: translate(-50%, -50%) rotate(4deg);
  animation: floating-pi-drift var(--egg-ms) ease-in-out both;
}

.floating-pi__digits {
  position: absolute;
  bottom: 12%;
  left: 0.75rem;
  font-family: ui-monospace, monospace;
  font-size: 1.375rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  opacity: 0.45;
  transform: rotate(-6deg);
  animation: floating-pi-trail var(--egg-ms) ease-in-out both;
}

@keyframes floating-pi-drift {
  0% {
    opacity: 0;
    transform: translate(-160%, -40%) rotate(-8deg);
  }
  15% {
    opacity: 0.75;
  }
  85% {
    opacity: 0.75;
  }
  100% {
    opacity: 0;
    transform: translate(60%, -60%) rotate(4deg);
  }
}

@keyframes floating-pi-trail {
  0%,
  20% {
    opacity: 0;
    transform: translateX(-2rem) rotate(-6deg);
  }
  60% {
    opacity: 0.45;
  }
  100% {
    opacity: 0;
    transform: translateX(8rem) rotate(-4deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .floating-pi__symbol,
  .floating-pi__digits {
    animation: none;
  }
}
</style>
