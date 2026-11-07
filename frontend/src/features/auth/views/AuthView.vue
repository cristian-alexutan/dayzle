<!-- AuthView: Google OAuth sign-in, guest continuation, and current account status. -->
<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import AppButton from '@/shared/components/AppButton.vue'
import AppCard from '@/shared/components/AppCard.vue'
import AppMessage from '@/shared/components/AppMessage.vue'
import AppSpinner from '@/shared/components/AppSpinner.vue'
import GameShell from '@/shared/components/GameShell.vue'

import {
  authErrorCode,
  useGoogleLoginMutation,
  useLogoutMutation,
  useSessionQuery,
} from '../api/queries'
import GoogleSignInButton from '../components/GoogleSignInButton.vue'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()

const sessionQuery = useSessionQuery()
const loginMutation = useGoogleLoginMutation()
const logoutMutation = useLogoutMutation()

const session = computed(() => sessionQuery.data.value)
const isSignedIn = computed(() => Boolean(session.value?.is_authenticated && session.value?.user))
const errorMessage = ref<string | null>(null)

function handleGoogleCredential(credential: string) {
  errorMessage.value = null
  loginMutation.mutate(credential, {
    onSuccess: () => {
      const next = typeof route.query.next === 'string' ? route.query.next : '/'
      router.push(next.startsWith('/') ? next : '/')
    },
    onError: (error) => {
      const code = authErrorCode(error)
      if (code === 'invalid_google_token') {
        errorMessage.value = t('auth.errors.invalidToken')
      } else if (code === 'google_auth_not_configured') {
        errorMessage.value = t('auth.errors.notConfigured')
      } else {
        errorMessage.value = t('auth.errors.generic')
      }
    },
  })
}

function handleLogout() {
  errorMessage.value = null
  logoutMutation.mutate()
}
</script>

<template>
  <GameShell :title="t('auth.title')">
    <AppSpinner v-if="sessionQuery.isPending.value" :aria-label="t('auth.loading')" />

    <AppCard v-else class="auth-card" data-test="login-card">
      <template #content>
        <div v-if="isSignedIn && session?.user" class="auth-card__body" data-test="signed-in-panel">
          <div class="auth-card__profile">
            <span class="auth-card__avatar" aria-hidden="true">
              <i class="pi pi-user" />
            </span>
            <div class="auth-card__identity">
              <p class="auth-card__name" data-test="user-display-name">
                {{ session.user.display_name }}
              </p>
              <p class="auth-card__email" data-test="user-email">
                {{ session.user.email }}
              </p>
            </div>
          </div>

          <AppMessage severity="success" data-test="signed-in-message">
            {{ t('auth.signedInAs', { name: session.user.display_name }) }}
          </AppMessage>
        </div>

        <div v-else class="auth-card__body" data-test="guest-panel">
          <p class="auth-card__subtitle">{{ t('auth.subtitle') }}</p>

          <AppMessage v-if="errorMessage" severity="error" data-test="auth-error">
            {{ errorMessage }}
          </AppMessage>

          <GoogleSignInButton @credential="handleGoogleCredential" />

          <div class="auth-card__guest-info" data-test="guest-badge">
            <i class="pi pi-id-card" aria-hidden="true" />
            <span>{{ t('auth.guestInfo') }}</span>
          </div>
        </div>
      </template>

      <template #footer>
        <div class="auth-card__footer">
          <AppButton
            v-if="isSignedIn"
            :label="t('auth.logout')"
            icon="pi pi-sign-out"
            severity="secondary"
            rounded
            :loading="logoutMutation.isPending.value"
            data-test="logout-button"
            @click="handleLogout"
          />
          <AppButton
            :label="isSignedIn ? t('auth.backHome') : t('auth.continueAsGuest')"
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
.auth-card {
  width: 100%;
  border: 1px solid var(--dz-border);
  background: var(--dz-surface);
}

.auth-card__body {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.15rem;
  text-align: center;
}

.auth-card__subtitle {
  margin: 0;
  color: var(--dz-text-muted);
  line-height: 1.5;
}

.auth-card__profile {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.auth-card__avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 999px;
  background: var(--dz-primary);
  color: var(--dz-on-primary);
  font-size: 1.25rem;
}

.auth-card__identity {
  text-align: left;
}

.auth-card__name {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--dz-text);
}

.auth-card__email {
  margin: 0.15rem 0 0;
  font-size: 0.9rem;
  color: var(--dz-text-muted);
}

.auth-card__guest-info {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.85rem;
  border-radius: 0.6rem;
  background: var(--dz-page);
  color: var(--dz-text-muted);
  font-size: 0.9rem;
}

.auth-card__footer {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.75rem;
}
</style>
