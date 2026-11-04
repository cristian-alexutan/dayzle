<!-- AppButton: the app's button, over PrimeVue's. Props and events pass straight through. -->
<script setup lang="ts">
import Button from 'primevue/button'
</script>

<template>
  <Button>
    <template v-for="name in Object.keys($slots)" #[name]="slotProps">
      <slot :name="name" v-bind="slotProps" />
    </template>
  </Button>
</template>
