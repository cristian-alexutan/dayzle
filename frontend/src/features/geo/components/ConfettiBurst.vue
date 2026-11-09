<!-- ConfettiBurst: confetti falling over the page once, for a very close guess. -->
<script setup lang="ts">
const PIECES = 80
const COLORS = ['primary', 'accent', 'present', 'primary-strong', 'accent-strong'] as const

/** Players who asked their system for less motion get no confetti. */
const reducedMotion =
  typeof window.matchMedia === 'function' &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches

/** Every piece gets its own place, size, timing and spin, picked once. */
const pieces = Array.from({ length: reducedMotion ? 0 : PIECES }, (_, index) => ({
  id: index,
  color: COLORS[index % COLORS.length],
  style: {
    left: `${Math.random() * 100}%`,
    width: `${6 + Math.random() * 6}px`,
    height: `${10 + Math.random() * 8}px`,
    animationDelay: `${Math.random() * 0.6}s`,
    animationDuration: `${2.2 + Math.random() * 1.6}s`,
    '--drift': `${(Math.random() - 0.5) * 30}vw`,
    '--spin': `${(Math.random() < 0.5 ? -1 : 1) * (360 + Math.random() * 720)}deg`,
  },
}))
</script>

<template>
  <div class="confetti" aria-hidden="true" data-test="confetti">
    <span
      v-for="piece in pieces"
      :key="piece.id"
      class="confetti__piece"
      :class="`confetti__piece--${piece.color}`"
      :style="piece.style"
    />
  </div>
</template>

<style scoped>
.confetti {
  position: fixed;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  z-index: 1000;
}

.confetti__piece {
  position: absolute;
  top: -5vh;
  border-radius: 2px;
  opacity: 0;
  animation-name: confetti-fall;
  animation-timing-function: cubic-bezier(0.25, 0.6, 0.5, 1);
  animation-fill-mode: forwards;
}

.confetti__piece--primary {
  background: var(--dz-primary);
}

.confetti__piece--accent {
  background: var(--dz-accent);
}

.confetti__piece--present {
  background: var(--dz-present);
}

.confetti__piece--primary-strong {
  background: var(--dz-primary-strong);
}

.confetti__piece--accent-strong {
  background: var(--dz-accent-strong);
}

@keyframes confetti-fall {
  0% {
    opacity: 1;
    transform: translate(0, 0) rotate(0deg);
  }
  85% {
    opacity: 1;
  }
  100% {
    opacity: 0;
    transform: translate(var(--drift), 110vh) rotate(var(--spin));
  }
}
</style>
