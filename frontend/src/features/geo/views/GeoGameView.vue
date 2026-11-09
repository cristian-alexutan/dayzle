<!-- GeoGameView: the daily GeoGuesser game inside the shared game frame. -->
<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import AppMessage from '@/shared/components/AppMessage.vue'
import AppSpinner from '@/shared/components/AppSpinner.vue'
import ErrorState from '@/shared/components/ErrorState.vue'
import GameShell from '@/shared/components/GameShell.vue'

import { errorCode, errorDetails, useGeoGameQuery, useGeoHeartbeat } from '../api/queries'

const DAY = 'today'

const { t, locale } = useI18n()

const query = useGeoGameQuery(DAY)

const game = computed(() => query.data.value)
const inProgress = computed(() => game.value?.status === 'in_progress')
const finished = computed(() => game.value?.status === 'completed')

const code = computed(() => errorCode(query.error.value))
const noPuzzle = computed(() => code.value === 'no_puzzle')
/** The region doesn't exist or is switched off: a setup problem, not a day without a game. */
const noRegion = computed(() => code.value === 'no_region')
/** Today's game was started in another region, which the backend names in the error. */
const lockedRegion = computed(() =>
  code.value === 'region_locked' ? String(errorDetails(query.error.value)?.region ?? '') : null,
)

useGeoHeartbeat(DAY, inProgress)

/** "Cluj-Napoca · duminică, 8 noiembrie": the region and the day, in the player's language. */
const subtitle = computed(() => {
  if (!game.value) return ''
  const [year, month, day] = game.value.date.split('-').map(Number) as [number, number, number]
  const date = new Intl.DateTimeFormat(locale.value, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  }).format(new Date(year, month - 1, day))
  return t('geo.subtitle', { region: game.value.region.name, date })
})
</script>

<template>
  <GameShell :title="t('geo.title')">
    <AppSpinner v-if="query.isPending.value" :aria-label="t('geo.loading')" />
    <AppMessage v-else-if="noPuzzle" severity="info" data-test="no-puzzle">
      {{ t('geo.noPuzzle') }}
    </AppMessage>
    <AppMessage v-else-if="lockedRegion !== null" severity="info" data-test="region-locked">
      {{ t('geo.regionLocked', { region: lockedRegion }) }}
    </AppMessage>
    <ErrorState
      v-else-if="query.isError.value"
      :message="t(noRegion ? 'geo.errors.noRegion' : 'geo.errors.generic')"
      :retryable="!noRegion"
      @retry="query.refetch()"
    />
    <template v-else-if="game">
      <p class="geo-game__subtitle" data-test="subtitle">{{ subtitle }}</p>
      <div class="geo-game__status">
        <span v-if="inProgress" data-test="round">
          {{ t('geo.round', { round: game.current_round, rounds: game.rounds }) }}
        </span>
        <span data-test="score">
          {{ t('geo.score', { score: game.total_score, max: game.max_score }) }}
        </span>
      </div>
      <AppMessage v-if="finished" severity="success" data-test="finished">
        {{ t('geo.finished', { score: game.total_score, max: game.max_score }) }}
      </AppMessage>
    </template>
  </GameShell>
</template>

<style scoped>
.geo-game__subtitle {
  margin: -0.5rem 0 0;
  color: var(--dz-text-muted);
  font-size: 0.875rem;
}

.geo-game__status {
  display: flex;
  justify-content: space-between;
  width: 100%;
  font-weight: 600;
}
</style>
