<!-- GeoResult: the end of the game: the score out of 5000, the time and every round on a map. -->
<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import ResultCard from '@/shared/components/ResultCard.vue'

import { useDistanceFormat } from '../composables/useDistanceFormat'
import type { GeoGame } from '../types'
import RevealMap from './RevealMap.vue'

const props = defineProps<{ game: GeoGame }>()

const { t } = useI18n()
const formatDistance = useDistanceFormat()

const result = computed(() => `${props.game.total_score}/${props.game.max_score}`)
const title = computed(() => t(props.game.solved ? 'geo.result.won' : 'geo.result.lost'))
</script>

<template>
  <section class="geo-result" data-test="result">
    <h2 class="geo-result__title">{{ title }}</h2>
    <ResultCard :result="result" :duration-ms="game.duration_ms" />
    <RevealMap :bounds="game.region.bounds" :results="game.results" numbered />
    <ol class="geo-result__rounds" :aria-label="t('geo.result.rounds')">
      <li v-for="round in game.results" :key="round.round" data-test="result-round">
        <span class="geo-result__round">{{ t('geo.result.round', { round: round.round }) }}</span>
        <span>{{ formatDistance(round.distance_m) }}</span>
        <span class="geo-result__score">{{ t('geo.points', { score: round.score }) }}</span>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.geo-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
}

.geo-result__title {
  margin: 0;
  font-size: 1.25rem;
}

.geo-result__rounds {
  width: 100%;
  margin: 0;
  padding: 0;
  list-style: none;
}

.geo-result__rounds li {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  padding: 0.4rem 0;
  border-bottom: 1px solid var(--dz-border);
}

.geo-result__round {
  font-weight: 600;
}

.geo-result__score {
  text-align: right;
}
</style>
