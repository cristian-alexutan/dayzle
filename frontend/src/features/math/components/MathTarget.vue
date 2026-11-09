<!-- MathTarget: the number to reach, shown large at the top of the board. -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'

defineProps<{ target: number }>()

const { t } = useI18n()
</script>

<template>
  <section class="math-target" :aria-label="t('math.targetLabel', { target })" data-test="target">
    <span class="math-target__label" aria-hidden="true">
      <i class="pi pi-bullseye" />
      {{ t('math.target') }}
    </span>
    <span class="math-target__value" aria-hidden="true">{{ target }}</span>
  </section>
</template>

<style scoped>
.math-target {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  box-sizing: border-box;
  padding: 0.875rem 1.25rem 1.125rem;
  border-radius: 1.375rem;
  background: var(--dz-primary);
  color: var(--dz-on-primary);
}

.math-target__label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.math-target__value {
  font-size: 4.75rem;
  font-weight: 900;
  line-height: 1;
  letter-spacing: -0.02em;
}
</style>
