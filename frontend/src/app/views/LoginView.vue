<!-- LoginView: Placeholder login page until Google OAuth is connected. -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import AppButton from '@/shared/components/AppButton.vue'
import AppCard from '@/shared/components/AppCard.vue'
import AppMessage from '@/shared/components/AppMessage.vue'
import GameShell from '@/shared/components/GameShell.vue'

const { t } = useI18n()
const router = useRouter()
</script>

<template>
  <GameShell :title="t('login.title')">
    <AppCard class="login-card" data-test="login-card">
      <template #content>
        <div class="login-card__body">
          <p class="login-card__subtitle">{{ t('login.subtitle') }}</p>
          <AppMessage severity="info" data-test="login-coming-soon">
            {{ t('login.comingSoon') }}
          </AppMessage>
        </div>
      </template>
      <template #footer>
        <div class="login-card__footer">
          <AppButton
            :label="t('home.backHome')"
            icon="pi pi-home"
            rounded
            data-test="login-back-home"
            @click="router.push('/')"
          />
        </div>
      </template>
    </AppCard>
  </GameShell>
</template>

<style scoped>
.login-card {
  width: 100%;
  border: 1px solid var(--dz-border);
  background: var(--dz-surface);
}

.login-card__body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.login-card__subtitle {
  margin: 0;
  color: var(--dz-text-muted);
  line-height: 1.5;
}

.login-card__footer {
  display: flex;
  justify-content: center;
}
</style>
