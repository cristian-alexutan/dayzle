<!-- AppHeader: Top bar with the theme and language controls. -->
<script setup lang="ts">
import { computed, watchEffect } from 'vue'
import { useI18n } from 'vue-i18n'

import AppButton from '@/shared/components/AppButton.vue'
import { useThemeStore } from '@/shared/stores/theme'

import { storeLocale, type AppLocale } from '../i18n'

const THEME_ICONS = { light: 'pi pi-sun', dark: 'pi pi-moon', auto: 'pi pi-desktop' }

const { t, locale } = useI18n({ useScope: 'global' })
const theme = useThemeStore()

const themeLabel = computed(() => t(`header.theme.${theme.mode}`))

watchEffect(() => {
  document.documentElement.lang = locale.value
})

function toggleLocale() {
  const next: AppLocale = locale.value === 'ro' ? 'en' : 'ro'
  locale.value = next
  storeLocale(next)
}
</script>

<template>
  <header class="app-header">
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
  </header>
</template>

<style scoped>
.app-header {
  display: flex;
  justify-content: flex-end;
  gap: 0.25rem;
  padding: 0.5rem;
}
</style>
