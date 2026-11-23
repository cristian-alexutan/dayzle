<!-- HowToPlay: the rules (info) button at the top of a game and the dialog with its rules. -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import AppButton from './AppButton.vue'
import AppDialog from './AppDialog.vue'
import GameActionButton from './GameActionButton.vue'

/** A group of rules under a heading; each rule is a PrimeIcons class and translated text. */
export interface HowToPlaySection {
  heading: string
  rules: { icon: string; text: string }[]
}

defineProps<{ sections: HowToPlaySection[] }>()
/** Bind it so the game can open the rules itself, or pause its clock while they're open. */
const visible = defineModel<boolean>('visible', { default: false })

const { t } = useI18n()
</script>

<template>
  <GameActionButton
    icon="pi pi-info-circle"
    :aria-label="t('common.howToPlay.title')"
    :title="t('common.howToPlay.title')"
    data-test="how-to-play"
    @click="visible = true"
  />
  <AppDialog
    v-model:visible="visible"
    :header="t('common.howToPlay.title')"
    :style="{ width: 'min(92vw, 28rem)' }"
  >
    <div class="how-to-play" data-test="how-to-play-rules">
      <template v-for="section in sections" :key="section.heading">
        <p class="how-to-play__heading">{{ section.heading }}</p>
        <ul class="how-to-play__list">
          <li v-for="(rule, index) in section.rules" :key="index">
            <i :class="rule.icon" aria-hidden="true" />
            <span>{{ rule.text }}</span>
          </li>
        </ul>
      </template>
      <AppButton
        class="how-to-play__close"
        :label="t('common.howToPlay.close')"
        rounded
        data-test="how-to-play-close"
        @click="visible = false"
      />
    </div>
  </AppDialog>
</template>

<style scoped>
.how-to-play {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.how-to-play__heading {
  margin: 0.25rem 0 0;
  font-weight: 700;
}

.how-to-play__list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.how-to-play__list li {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
}

.how-to-play__list i {
  margin-top: 0.2rem;
  color: var(--dz-primary);
}

.how-to-play__close {
  align-self: center;
  margin-top: 0.5rem;
  padding-inline: 1.5rem;
}
</style>
