<!-- GamePlaceholderView: Shown for games whose frontend page is not yet merged on main. -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import AppButton from '@/shared/components/AppButton.vue'
import AppMessage from '@/shared/components/AppMessage.vue'
import GameShell from '@/shared/components/GameShell.vue'

defineProps<{
  gameKey: 'logic' | 'trivia' | 'geo'
}>()

const { t } = useI18n()
const router = useRouter()
</script>

<template>
  <GameShell :title="t(`home.games.${gameKey}.title`)">
    <AppMessage severity="info" data-test="game-coming-soon">
      {{ t('home.comingSoon') }}
    </AppMessage>
    <AppButton
      :label="t('login.backHome')"
      icon="pi pi-home"
      rounded
      data-test="game-back-home"
      @click="router.push('/')"
    />
  </GameShell>
</template>
