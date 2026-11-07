<!-- GoogleSignInButton: Loads Google Identity Services when configured and renders the sign-in button. -->
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import AppMessage from '@/shared/components/AppMessage.vue'

const PLACEHOLDER_CLIENT_ID = 'your-google-client-id.apps.googleusercontent.com'
const GIS_SCRIPT_SRC = 'https://accounts.google.com/gsi/client'

const emit = defineEmits<{
  credential: [token: string]
}>()

const { t } = useI18n()

const container = ref<HTMLElement | null>(null)
const clientId = (import.meta.env.VITE_GOOGLE_CLIENT_ID ?? '').trim()
const isConfigured = computed(() => Boolean(clientId) && clientId !== PLACEHOLDER_CLIENT_ID)

interface GoogleAccountsId {
  initialize: (config: {
    client_id: string
    callback: (response: { credential?: string }) => void
  }) => void
  renderButton: (parent: HTMLElement, options: Record<string, unknown>) => void
}

function getGoogleAccountsId(): GoogleAccountsId | undefined {
  const win = window as unknown as {
    google?: { accounts?: { id?: GoogleAccountsId } }
  }
  return win.google?.accounts?.id
}

function renderGoogleButton() {
  const gis = getGoogleAccountsId()
  if (!gis || !container.value) return
  gis.initialize({
    client_id: clientId,
    callback: (response) => {
      if (response.credential) {
        emit('credential', response.credential)
      }
    },
  })
  gis.renderButton(container.value, {
    theme: 'outline',
    size: 'large',
    shape: 'pill',
    width: 280,
  })
}

onMounted(() => {
  if (!isConfigured.value) return
  if (getGoogleAccountsId()) {
    renderGoogleButton()
    return
  }
  const existing = document.querySelector<HTMLScriptElement>(`script[src="${GIS_SCRIPT_SRC}"]`)
  if (existing) {
    existing.addEventListener('load', renderGoogleButton, { once: true })
    return
  }
  const script = document.createElement('script')
  script.src = GIS_SCRIPT_SRC
  script.async = true
  script.defer = true
  script.addEventListener('load', renderGoogleButton, { once: true })
  document.head.appendChild(script)
})
</script>

<template>
  <div class="google-signin" data-test="google-signin">
    <div
      v-if="isConfigured"
      ref="container"
      class="google-signin__button"
      data-test="google-button-container"
    />
    <AppMessage v-else severity="info" data-test="google-unconfigured">
      {{ t('auth.unconfigured') }}
    </AppMessage>
  </div>
</template>

<style scoped>
.google-signin {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

.google-signin__button {
  display: flex;
  justify-content: center;
  min-height: 2.75rem;
}
</style>
