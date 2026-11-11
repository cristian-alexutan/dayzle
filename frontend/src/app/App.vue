<script setup lang="ts">
import AppHeader from './layouts/AppHeader.vue'
</script>

<template>
  <div class="app-layout">
    <AppHeader />
    <div class="app-layout__content">
      <RouterView />
    </div>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-layout__content {
  flex: 1;
  padding-top: 1rem;
}
</style>
