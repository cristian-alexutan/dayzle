<!-- LogicTutorial: the rules and controls, shown the first time and from the help button. -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import AppButton from '@/shared/components/AppButton.vue'
import AppDialog from '@/shared/components/AppDialog.vue'

const visible = defineModel<boolean>('visible', { required: true })

const { t } = useI18n()

const RULES = [
  { icon: 'pi pi-sun', key: 'oneSun' },
  { icon: 'pi pi-th-large', key: 'regions' },
  { icon: 'pi pi-ban', key: 'noTouching' },
]

const CONTROLS = [
  { icon: 'pi pi-times', key: 'mark' },
  { icon: 'pi pi-sun', key: 'sun' },
  { icon: 'pi pi-bolt', key: 'score' },
]
</script>

<template>
  <AppDialog
    v-model:visible="visible"
    :header="t('logic.tutorial.title')"
    :style="{ width: 'min(92vw, 28rem)' }"
  >
    <div class="logic-tutorial" data-test="tutorial">
      <p class="logic-tutorial__heading">{{ t('logic.tutorial.rulesHeading') }}</p>
      <ul class="logic-tutorial__list">
        <li v-for="rule in RULES" :key="rule.key">
          <i :class="rule.icon" aria-hidden="true" />
          <span>{{ t(`logic.tutorial.rules.${rule.key}`) }}</span>
        </li>
      </ul>
      <p class="logic-tutorial__heading">{{ t('logic.tutorial.controlsHeading') }}</p>
      <ul class="logic-tutorial__list">
        <li v-for="control in CONTROLS" :key="control.key">
          <i :class="control.icon" aria-hidden="true" />
          <span>{{ t(`logic.tutorial.controls.${control.key}`) }}</span>
        </li>
      </ul>
      <AppButton
        class="logic-tutorial__start"
        :label="t('logic.tutorial.start')"
        rounded
        data-test="tutorial-start"
        @click="visible = false"
      />
    </div>
  </AppDialog>
</template>

<style scoped>
.logic-tutorial {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.logic-tutorial__heading {
  margin: 0.25rem 0 0;
  font-weight: 700;
}

.logic-tutorial__list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.logic-tutorial__list li {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
}

.logic-tutorial__list i {
  margin-top: 0.2rem;
  color: var(--dz-sun);
}

.logic-tutorial__start {
  align-self: center;
  margin-top: 0.5rem;
  padding-inline: 1.5rem;
}
</style>
