<!-- AppMessage: the app's inline message, over PrimeVue's. Props pass straight through. -->
<script setup lang="ts">
import Message from 'primevue/message'
</script>

<template>
  <Message :closable="false">
    <template v-for="name in Object.keys($slots)" #[name]="slotProps">
      <slot :name="name" v-bind="slotProps" />
    </template>
  </Message>
</template>
