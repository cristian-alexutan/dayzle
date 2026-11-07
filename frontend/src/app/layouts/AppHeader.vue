<!-- AppHeader: Top navigation bar with brand logo, home link, user/guest status, theme and language controls. -->
<script setup lang="ts">
import { computed, watchEffect } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { useLogoutMutation, useSessionQuery } from '@/features/auth'
import AppButton from '@/shared/components/AppButton.vue'
import { useThemeStore } from '@/shared/stores/theme'

import { storeLocale, type AppLocale } from '../i18n'

const THEME_ICONS = { light: 'pi pi-sun', dark: 'pi pi-moon', auto: 'pi pi-desktop' }

const { t, locale } = useI18n({ useScope: 'global' })
const theme = useThemeStore()
const router = useRouter()

const sessionQuery = useSessionQuery()
const logoutMutation = useLogoutMutation()

const session = computed(() => sessionQuery.data.value)
const isSignedIn = computed(() => Boolean(session.value?.is_authenticated && session.value?.user))
const themeLabel = computed(() => t(`header.theme.${theme.mode}`))

watchEffect(() => {
  document.documentElement.lang = locale.value
})

function toggleLocale() {
  const next: AppLocale = locale.value === 'ro' ? 'en' : 'ro'
  locale.value = next
  storeLocale(next)
}

function handleLogout() {
  logoutMutation.mutate()
}
</script>

<template>
  <header class="app-header">
    <nav class="app-header__nav" :aria-label="t('header.nav')">
      <div class="app-header__left">
        <RouterLink to="/" class="app-header__brand" data-test="brand-link">
          <i class="pi pi-sparkles app-header__brand-icon" aria-hidden="true" />
          <span>Dayzle</span>
        </RouterLink>
        <RouterLink to="/" class="app-header__link" data-test="home-link">
          <i class="pi pi-home" aria-hidden="true" />
          <span>{{ t('header.home') }}</span>
        </RouterLink>
      </div>

      <div class="app-header__actions">
        <template v-if="isSignedIn && session?.user">
          <RouterLink to="/login" class="app-header__user" data-test="user-chip">
            <i class="pi pi-user" aria-hidden="true" />
            <span>{{ session.user.display_name }}</span>
          </RouterLink>
          <AppButton
            :label="t('header.logout')"
            icon="pi pi-sign-out"
            text
            severity="secondary"
            :loading="logoutMutation.isPending.value"
            data-test="logout-link"
            @click="handleLogout"
          />
        </template>
        <AppButton
          v-else
          :label="t('header.login')"
          icon="pi pi-user"
          text
          severity="secondary"
          data-test="login-link"
          @click="router.push('/login')"
        />

        <AppButton
          :icon="THEME_ICONS[theme.mode]"
          :aria-label="themeLabel"
          :title="themeLabel"
          text
          severity="secondary"
          data-test="theme"
          @click="theme.cycle()"
        />
        <AppButton
          :label="locale.toUpperCase()"
          :aria-label="t('header.language')"
          :title="t('header.language')"
          text
          severity="secondary"
          data-test="language"
          @click="toggleLocale"
        />
      </div>
    </nav>
  </header>
</template>

<style scoped>
.app-header {
  border-bottom: 1px solid var(--dz-border);
  background: var(--dz-surface);
}

.app-header__nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  max-width: 64rem;
  margin: 0 auto;
  padding: 0.5rem 1rem;
}

.app-header__left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.app-header__brand {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 1.25rem;
  font-weight: 800;
  letter-spacing: 0.02em;
  color: var(--dz-text);
  text-decoration: none;
}

.app-header__brand-icon {
  color: var(--dz-primary-strong);
}

.app-header__link {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.65rem;
  border-radius: 0.5rem;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--dz-text-muted);
  text-decoration: none;
  transition:
    color 0.15s ease,
    background-color 0.15s ease;
}

.app-header__link:hover,
.app-header__link.router-link-exact-active {
  color: var(--dz-text);
  background: var(--dz-page);
}

.app-header__actions {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.app-header__user {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.7rem;
  border-radius: 999px;
  background: var(--dz-page);
  color: var(--dz-text);
  font-size: 0.9rem;
  font-weight: 600;
  text-decoration: none;
}

.app-header__user:hover {
  background: var(--dz-primary);
  color: var(--dz-on-primary);
}
</style>
