<!-- TriviaRules: how the quiz works, shown the first time and from the rules button. -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import AppButton from '@/shared/components/AppButton.vue'
import AppDialog from '@/shared/components/AppDialog.vue'

const visible = defineModel<boolean>('visible', { required: true })

const { t } = useI18n()

const RULES = [
  { icon: 'pi pi-list', key: 'questions' },
  { icon: 'pi pi-check-circle', key: 'answer' },
  { icon: 'pi pi-lock', key: 'final' },
]

const SCORING = [
  { icon: 'pi pi-star', key: 'points' },
  { icon: 'pi pi-calendar', key: 'once' },
  { icon: 'pi pi-stopwatch', key: 'time' },
]
</script>

<template>
  <AppDialog
    v-model:visible="visible"
    :header="t('trivia.rules.title')"
    :style="{ width: 'min(92vw, 28rem)' }"
  >
    <div class="trivia-rules" data-test="rules">
      <p class="trivia-rules__heading">{{ t('trivia.rules.rulesHeading') }}</p>
      <ul class="trivia-rules__list">
        <li v-for="rule in RULES" :key="rule.key">
          <i :class="rule.icon" aria-hidden="true" />
          <span>{{ t(`trivia.rules.rules.${rule.key}`) }}</span>
        </li>
      </ul>
      <p class="trivia-rules__heading">{{ t('trivia.rules.scoringHeading') }}</p>
      <ul class="trivia-rules__list">
        <li v-for="item in SCORING" :key="item.key">
          <i :class="item.icon" aria-hidden="true" />
          <span>{{ t(`trivia.rules.scoring.${item.key}`) }}</span>
        </li>
      </ul>
      <AppButton
        class="trivia-rules__start"
        :label="t('trivia.rules.start')"
        rounded
        data-test="rules-start"
        @click="visible = false"
      />
    </div>
  </AppDialog>
</template>

<style scoped>
.trivia-rules {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.trivia-rules__heading {
  margin: 0.25rem 0 0;
  font-weight: 700;
}

.trivia-rules__list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.trivia-rules__list li {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
}

.trivia-rules__list i {
  margin-top: 0.2rem;
  color: var(--dz-primary);
}

.trivia-rules__start {
  align-self: center;
  margin-top: 0.5rem;
  padding-inline: 1.5rem;
}
</style>
