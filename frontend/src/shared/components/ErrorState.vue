<!-- ErrorState: Generic error message, with a retry button when the action can be retried. -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import AppButton from './AppButton.vue'
import AppMessage from './AppMessage.vue'

defineProps<{ message: string; retryable?: boolean }>()
defineEmits<{ retry: [] }>()

const { t } = useI18n()
</script>

<template>
  <div class="error-state">
    <AppMessage severity="error">{{ message }}</AppMessage>
    <AppButton v-if="retryable" :label="t('common.retry')" @click="$emit('retry')" />
  </div>
</template>

<style scoped>
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}
</style>
