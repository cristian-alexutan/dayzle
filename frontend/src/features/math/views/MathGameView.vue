<!-- MathGameView: the daily Math game inside the shared game frame. -->
<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import AppMessage from '@/shared/components/AppMessage.vue'
import AppSpinner from '@/shared/components/AppSpinner.vue'
import ErrorState from '@/shared/components/ErrorState.vue'
import GameShell from '@/shared/components/GameShell.vue'

import { errorCode, useMathGameQuery } from '../api/queries'

const DAY = 'today'

const { t } = useI18n()

const query = useMathGameQuery(DAY)

const game = computed(() => query.data.value)
const noPuzzle = computed(() => errorCode(query.error.value) === 'no_puzzle')
</script>

<template>
  <GameShell :title="t('math.title')">
    <AppSpinner v-if="query.isPending.value" :aria-label="t('math.loading')" />
    <AppMessage v-else-if="noPuzzle" severity="info" data-test="no-puzzle">
      {{ t('math.noPuzzle') }}
    </AppMessage>
    <ErrorState
      v-else-if="query.isError.value"
      :message="t('math.errors.generic')"
      retryable
      @retry="query.refetch()"
    />
    <template v-else-if="game">
      <p class="math-game__target" data-test="target">
        {{ t('math.target') }}: <strong>{{ game.target }}</strong>
      </p>
      <ul class="math-game__numbers" :aria-label="t('math.numbers')" data-test="numbers">
        <li v-for="(number, index) in game.numbers" :key="index">{{ number }}</li>
      </ul>
    </template>
  </GameShell>
</template>

<style scoped>
.math-game__target {
  margin: 0;
  font-size: 1.25rem;
}

.math-game__numbers {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.5rem;
  margin: 0;
  padding: 0;
  list-style: none;
}
</style>
