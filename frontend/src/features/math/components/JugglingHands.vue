<!-- JugglingHands: the 67 easter egg, two open hands moving up and down in turn over the board. -->
<script setup lang="ts">
import { EGG_MS } from '../composables/useEasterEggs'

const HANDS = ['left', 'right'] as const
</script>

<template>
  <div class="juggling-hands" :style="{ '--egg-ms': `${EGG_MS}ms` }" aria-hidden="true">
    <div class="juggling-hands__pair">
      <div
        v-for="side in HANDS"
        :key="side"
        class="juggling-hands__hand"
        :class="`juggling-hands__hand--${side}`"
        data-test="hand"
      >
        <svg width="112" height="100" viewBox="0 0 120 108" fill="none">
          <rect x="24" y="22" width="15" height="34" rx="7.5" />
          <rect x="41" y="14" width="15" height="40" rx="7.5" />
          <rect x="58" y="14" width="15" height="40" rx="7.5" />
          <rect x="75" y="20" width="15" height="36" rx="7.5" />
          <path d="M18 50 Q18 86 58 86 Q98 86 102 54 L102 46 Q92 40 86 50 L20 50 Z" />
          <path d="M86 50 Q94 34 106 38 Q112 42 104 56" />
          <path class="juggling-hands__line" d="M38 66 Q58 74 80 66" />
          <rect class="juggling-hands__cuff" x="34" y="84" width="48" height="16" rx="6" />
        </svg>
      </div>
    </div>
  </div>
</template>

<style scoped>
.juggling-hands {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  border-radius: 1.375rem;
  background: color-mix(in srgb, var(--dz-page) 72%, transparent);
  pointer-events: none;
  animation: juggling-hands-fade var(--egg-ms) ease-in-out both;
}

.juggling-hands__pair {
  display: flex;
  gap: 1.125rem;
}

.juggling-hands__hand {
  /* Four bobs in the egg's time; the right hand starts half a bob later. */
  animation: juggling-hands-bob calc(var(--egg-ms) / 4) ease-in-out infinite alternate;
}

.juggling-hands__hand--right {
  animation-delay: calc(var(--egg-ms) / -8);
}

.juggling-hands__hand--right svg {
  transform: scaleX(-1);
}

svg {
  stroke: var(--dz-text);
  stroke-width: 3.5;
  stroke-linejoin: round;
  stroke-linecap: round;
  fill: var(--dz-surface);
}

.juggling-hands__line {
  fill: none;
  stroke-width: 2.5;
}

.juggling-hands__cuff {
  fill: var(--dz-primary);
}

@keyframes juggling-hands-bob {
  from {
    transform: translateY(-26px);
  }
  to {
    transform: translateY(26px);
  }
}

@keyframes juggling-hands-fade {
  0% {
    opacity: 0;
    transform: scale(0.85);
  }
  12%,
  88% {
    opacity: 1;
    transform: scale(1);
  }
  100% {
    opacity: 0;
  }
}

/* One still frame instead of the movement. */
@media (prefers-reduced-motion: reduce) {
  .juggling-hands,
  .juggling-hands__hand {
    animation: none;
  }
}
</style>
