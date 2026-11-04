<!-- AppDialog: the app's modal dialog, over PrimeVue's. Use it with v-model:visible. -->
<script setup lang="ts">
import Dialog from 'primevue/dialog'
</script>

<template>
  <Dialog modal dismissable-mask :draggable="false">
    <template v-for="name in Object.keys($slots)" #[name]="slotProps">
      <slot :name="name" v-bind="slotProps" />
    </template>
  </Dialog>
</template>
