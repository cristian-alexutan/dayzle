<!-- AppDialog: the app's modal dialog, over PrimeVue's. Use it with v-model:visible. -->
<script setup lang="ts">
import Dialog from 'primevue/dialog'

const CLOSE_BUTTON = {
  severity: 'secondary',
  text: true,
  iconOnly: true,
  class: 'app-dialog__close',
}
</script>

<template>
  <Dialog modal dismissable-mask :draggable="false" :close-button-props="CLOSE_BUTTON">
    <template v-for="name in Object.keys($slots)" #[name]="slotProps">
      <slot :name="name" v-bind="slotProps" />
    </template>
  </Dialog>
</template>

<!-- Not scoped: PrimeVue renders the dialog at the end of the page, outside this component. -->
<style>
.app-dialog__close.p-button {
  --p-button-text-secondary-color: var(--dz-accent-strong);
  --p-button-text-secondary-hover-color: var(--dz-accent);
  --p-button-text-secondary-active-color: var(--dz-accent);
  --p-button-text-secondary-hover-background: transparent;
  --p-button-text-secondary-active-background: transparent;
  transition: transform 0.15s;
}

.app-dialog__close.p-button:hover,
.app-dialog__close.p-button:focus-visible {
  outline: none;
  transform: scale(1.2);
}
</style>
