<!--
  HowToPlay: the rules (info) button at the top of a game and the dialog with its rules. The
  rules open by themselves the first time a player sees the game; after that, only from the
  button.
-->
<script setup lang="ts">
import { watch } from 'vue'
import { useI18n } from 'vue-i18n'

import AppButton from './AppButton.vue'
import AppDialog from './AppDialog.vue'
import GameActionButton from './GameActionButton.vue'

/** A group of rules under a heading; each rule is a PrimeIcons class and translated text. */
export interface HowToPlaySection {
  heading: string
  rules: { icon: string; text: string }[]
}

const props = withDefaults(
  defineProps<{
    sections: HowToPlaySection[]
    /** The game's key, e.g. `word`: whether its rules were seen is remembered under it. */
    game: string
    /**
     * Whether the rules may open by themselves now, e.g. only while the game is unfinished. They
     * still open by themselves only once per browser.
     */
    autoOpen?: boolean
  }>(),
  { autoOpen: true },
)
/** Bind it so the game can pause its clock (or its keyboard) while the rules are open. */
const visible = defineModel<boolean>('visible', { default: false })

const { t } = useI18n()

const seenKey = () => `dayzle.${props.game}.rulesSeen`

function seen(): boolean {
  try {
    return localStorage.getItem(seenKey()) === 'yes'
  } catch {
    // Storage is blocked (e.g. some private windows): show the rules, they just aren't remembered.
    return false
  }
}

function rememberSeen() {
  try {
    localStorage.setItem(seenKey(), 'yes')
  } catch {
    // Not remembered: the rules open by themselves again next time.
  }
}

let opened = false
watch(
  () => props.autoOpen,
  (allowed) => {
    if (!allowed || opened || seen()) return
    opened = true
    visible.value = true
  },
  { immediate: true },
)

// Closing the rules, however they were opened, means the player has seen them.
watch(visible, (isVisible, wasVisible) => {
  if (wasVisible && !isVisible) rememberSeen()
})
</script>

<template>
  <GameActionButton
    icon="pi pi-info-circle"
    :aria-label="t('common.howToPlay.title')"
    :title="t('common.howToPlay.title')"
    data-test="how-to-play"
    @click="visible = true"
  />
  <AppDialog v-model:visible="visible" :header="t('common.howToPlay.title')" size="rules">
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
