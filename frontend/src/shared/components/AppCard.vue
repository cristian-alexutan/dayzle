<!-- AppCard: the app's card, over PrimeVue's. Props and slots pass straight through. -->
<script setup lang="ts">
import Card from 'primevue/card'
</script>

<template>
  <Card>
    <template v-for="name in Object.keys($slots)" #[name]="slotProps">
      <slot :name="name" v-bind="slotProps" />
    </template>
  </Card>
</template>
