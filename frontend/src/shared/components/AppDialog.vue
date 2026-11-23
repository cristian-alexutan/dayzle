<!-- AppDialog: the app's modal dialog, over PrimeVue's. Use it with v-model:visible. -->
<script setup lang="ts">
import Dialog from 'primevue/dialog'

/**
 * `result` (a game's end: same width) and `rules` (how to play: same width and height) keep
 * every game's dialogs of that kind alike.
 */
defineProps<{ size?: 'result' | 'rules' }>()

const CLOSE_BUTTON = {
  severity: 'secondary',
  text: true,
  rounded: true,
  class: 'app-dialog__close',
}
</script>

<template>
  <Dialog
    class="app-dialog"
    :class="size && `app-dialog--${size}`"
    modal
    dismissable-mask
    :draggable="false"
    :close-button-props="CLOSE_BUTTON"
  >
    <template v-for="name in Object.keys($slots)" #[name]="slotProps">
      <slot :name="name" v-bind="slotProps" />
    </template>
  </Dialog>
</template>

<!-- Not scoped: PrimeVue renders the dialog at the end of the page, outside this component. -->
<style>
/* Every result dialog has the same width; its height follows what the game shows. */
.app-dialog--result {
  width: min(90vw, 24rem);
}

/* Every rules dialog has the same size; longer rules scroll inside it. */
.app-dialog--rules {
  width: min(92vw, 28rem);
  height: min(85vh, 36rem);
}

/* The title is centered in the dialog, so it needs the X's width on its other side too. */
.app-dialog .p-dialog-title {
  flex: 1;
  margin-inline-start: 2.75rem;
  text-align: center;
}

.app-dialog__close.p-button {
  width: 2.75rem;
  height: 2.75rem;
  --p-button-text-secondary-color: var(--dz-accent-strong);
  --p-button-text-secondary-hover-color: var(--dz-accent-strong);
  --p-button-text-secondary-active-color: var(--dz-accent-strong);
  --p-button-text-secondary-hover-background: transparent;
  --p-button-text-secondary-active-background: transparent;
  transition: transform 0.15s;
}

.app-dialog__close.p-button svg {
  width: 1.5rem;
  height: 1.5rem;
}

.app-dialog__close.p-button:hover,
.app-dialog__close.p-button:focus-visible {
  outline: none;
  transform: scale(1.2);
}
</style>
