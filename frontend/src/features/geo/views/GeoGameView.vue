<!-- GeoGameView: the daily GeoGuesser game inside the shared game frame. -->
<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import AppButton from '@/shared/components/AppButton.vue'
import AppMessage from '@/shared/components/AppMessage.vue'
import AppSpinner from '@/shared/components/AppSpinner.vue'
import ErrorState from '@/shared/components/ErrorState.vue'
import GameShell from '@/shared/components/GameShell.vue'

import {
  errorCode,
  errorDetails,
  useGeoGameQuery,
  useGeoHeartbeat,
  useGuessMutation,
  useRegionsQuery,
} from '../api/queries'
import GeoMap from '../components/GeoMap.vue'
import ConfettiBurst from '../components/ConfettiBurst.vue'
import GeoResult from '../components/GeoResult.vue'
import RevealMap from '../components/RevealMap.vue'
import StreetViewPanorama from '../components/StreetViewPanorama.vue'
import { useDistanceFormat } from '../composables/useDistanceFormat'
import { usePinPlacement } from '../composables/usePinPlacement'
import type { RegionKey, RoundResult } from '../types'

const DAY = 'today'
/** Errors that mean the saved game moved on (another tab, a double click): reload it. */
const STALE_CODES = new Set(['already_answered', 'already_played', 'region_locked', 'invalid'])
/** A guess closer than this to the real spot is celebrated with confetti. */
const CONFETTI_UNDER_M = 100

const { t } = useI18n()
const formatDistance = useDistanceFormat()

/** The region played: the backend's default one, unless the player continues in another. */
const region = ref<RegionKey>(undefined)

const query = useGeoGameQuery(DAY, region)
const guess = useGuessMutation(DAY, region)

const game = computed(() => query.data.value)
const inProgress = computed(() => game.value?.status === 'in_progress')

const code = computed(() => errorCode(query.error.value))
const noPuzzle = computed(() => code.value === 'no_puzzle')
/** The region doesn't exist or is switched off: a setup problem, not a day without a game. */
const noRegion = computed(() => code.value === 'no_region')

/** The key of the region today's game was started in, when it isn't the one opened. */
const lockedKey = computed(() => {
  if (code.value !== 'region_locked') return null
  const key = errorDetails(query.error.value)?.region
  return typeof key === 'string' && key ? key : null
})
const regions = useRegionsQuery(() => lockedKey.value !== null)
/** Its name for the player, or the key until the regions have loaded. */
const lockedName = computed(
  () => regions.data.value?.find((item) => item.key === lockedKey.value)?.name ?? lockedKey.value,
)

/** Finish today's game where it was started: the backend accepts that region. */
function continueInLockedRegion() {
  region.value = lockedKey.value ?? undefined
}

useGeoHeartbeat(DAY, inProgress)

const { pin, outside, place, clear } = usePinPlacement({
  bounds: () => game.value?.region.bounds,
  round: () => game.value?.current_round,
})

/**
 * The round just guessed, shown on the reveal map until the player moves on. After the fifth
 * guess the game is already finished, and the end screen comes after this reveal.
 */
const revealed = ref<RoundResult | null>(null)
const phase = computed(() => {
  if (revealed.value) return 'reveal'
  return inProgress.value ? 'guess' : 'result'
})

/**
 * What the main window shows while guessing: the panorama, or the map to put the pin on. Both
 * stay mounted once opened, so switching keeps where the player looked and the pin.
 */
const view = ref<'panorama' | 'map'>('panorama')
/** The map is made the first time it's opened, when its window has a size to fit the region. */
const mapOpened = ref(false)

function openMap() {
  view.value = 'map'
  mapOpened.value = true
}

function backToPanorama() {
  view.value = 'panorama'
}

// Every round starts on its panorama, with a fresh map.
watch(
  () => game.value?.current_round,
  () => {
    view.value = 'panorama'
    mapOpened.value = false
  },
)

/** Shown when the server refuses a guess or can't be reached. */
const guessError = ref<string | null>(null)

function sendGuess() {
  const round = game.value?.current_round
  if (!pin.value || !round) return
  guessError.value = null
  guess.mutate(
    { round, ...pin.value },
    {
      onSuccess: (updated) => {
        revealed.value = updated.results.find((result) => result.round === round) ?? null
        clear()
      },
      onError: (error) => {
        const errorCodeValue = errorCode(error)
        if (errorCodeValue === 'invalid' && errorDetails(error)?.bounds === 'outside') {
          guessError.value = t('geo.errors.outside', { region: game.value?.region.name })
        } else if (errorCodeValue && STALE_CODES.has(errorCodeValue)) {
          guessError.value = t('geo.errors.stale')
          clear()
          query.refetch()
        } else {
          // Network or server trouble: keep the pin so the player can try again.
          guessError.value = t('geo.errors.generic')
        }
      },
    },
  )
}

function nextRound() {
  revealed.value = null
  guessError.value = null
  view.value = 'panorama'
  mapOpened.value = false
}

const hint = computed(() => {
  if (guessError.value) return guessError.value
  if (outside.value) return t('geo.errors.outside', { region: game.value?.region.name })
  return null
})

/** The title around its first "o", which is drawn as a globe: "Ge", "Guesser". */
const titleParts = computed(() => {
  const title = t('geo.title')
  const at = title.indexOf('o')
  return at < 0 ? null : [title.slice(0, at), title.slice(at + 1)]
})
</script>

<template>
  <GameShell :title="t('geo.title')" wide>
    <template #title>
      <span v-if="titleParts" class="geo-title" data-test="title">
        <span class="geo-title__label">{{ t('geo.title') }}</span>
        <span aria-hidden="true">
          {{ titleParts[0] }}<i class="pi pi-globe geo-title__globe" />{{ titleParts[1] }}
        </span>
      </span>
      <template v-else>{{ t('geo.title') }}</template>
    </template>
    <AppSpinner v-if="query.isPending.value" :aria-label="t('geo.loading')" />
    <AppMessage v-else-if="noPuzzle" severity="info" data-test="no-puzzle">
      {{ t('geo.noPuzzle') }}
    </AppMessage>
    <div v-else-if="lockedKey !== null" class="geo-game__locked" data-test="region-locked">
      <AppMessage severity="info">
        {{ t('geo.regionLocked', { region: lockedName }) }}
      </AppMessage>
      <AppButton
        :label="t('geo.continueIn', { region: lockedName })"
        icon="pi pi-arrow-right"
        icon-pos="right"
        data-test="continue-region"
        @click="continueInLockedRegion"
      />
    </div>
    <ErrorState
      v-else-if="query.isError.value"
      :message="t(noRegion ? 'geo.errors.noRegion' : 'geo.errors.generic')"
      :retryable="!noRegion"
      @retry="query.refetch()"
    />
    <template v-else-if="game">
      <template v-if="phase === 'guess' && game.panorama_id">
        <div class="geo-game__status">
          <span data-test="round">
            {{ t('geo.round', { round: game.current_round, rounds: game.rounds }) }}
          </span>
          <span data-test="score">
            {{ t('geo.score', { score: game.total_score, max: game.max_score }) }}
          </span>
        </div>
        <!-- Both layers keep their size while hidden, so Google never draws into a 0×0 box. -->
        <div class="geo-game__stage geo-frame--stage" :data-view="view" data-test="stage">
          <StreetViewPanorama
            class="geo-game__layer"
            :class="{ 'geo-game__layer--hidden': view !== 'panorama' }"
            :panorama-id="game.panorama_id"
          />
          <GeoMap
            v-if="mapOpened"
            class="geo-game__layer"
            :class="{ 'geo-game__layer--hidden': view !== 'map' }"
            :bounds="game.region.bounds"
            :pin="pin"
            :disabled="guess.isPending.value"
            :aria-label="t('geo.map.guess')"
            @place="place"
          />
        </div>

        <p v-if="hint" class="geo-game__error" role="alert" data-test="guess-error">
          <i class="pi pi-exclamation-circle" aria-hidden="true" />
          <span>{{ hint }}</span>
        </p>
        <template v-if="view === 'panorama'">
          <AppButton
            class="geo-game__action"
            :label="t('geo.openMap')"
            icon="pi pi-map"
            data-test="open-map"
            @click="openMap"
          />
        </template>
        <template v-else>
          <p v-if="!hint" class="geo-game__help">{{ t('geo.placePin') }}</p>
          <div class="geo-game__actions">
            <AppButton
              :label="t('geo.backToPanorama')"
              icon="pi pi-image"
              severity="secondary"
              outlined
              data-test="back-to-panorama"
              @click="backToPanorama"
            />
            <AppButton
              :label="t('geo.guess')"
              icon="pi pi-map-marker"
              :disabled="!pin || guess.isPending.value"
              :loading="guess.isPending.value"
              data-test="guess"
              @click="sendGuess"
            />
          </div>
        </template>
      </template>

      <template v-else-if="phase === 'reveal' && revealed">
        <ConfettiBurst v-if="revealed.distance_m < CONFETTI_UNDER_M" :key="revealed.round" />
        <div class="geo-game__status">
          <span data-test="round">
            {{ t('geo.round', { round: revealed.round, rounds: game.rounds }) }}
          </span>
          <span data-test="score">
            {{ t('geo.score', { score: game.total_score, max: game.max_score }) }}
          </span>
        </div>
        <RevealMap
          class="geo-frame--stage"
          :bounds="game.region.bounds"
          :results="[revealed]"
          :aria-label="t('geo.map.reveal')"
        />
        <p class="geo-game__reveal" data-test="reveal">
          <strong>{{ t('geo.points', { score: revealed.score }) }}</strong>
          <span>{{ t('geo.distance', { distance: formatDistance(revealed.distance_m) }) }}</span>
        </p>
        <AppButton
          class="geo-game__action"
          :label="t(inProgress ? 'geo.next' : 'geo.seeResult')"
          icon="pi pi-arrow-right"
          icon-pos="right"
          data-test="next"
          @click="nextRound"
        />
      </template>

      <GeoResult v-else-if="phase === 'result'" :game="game" />
    </template>
  </GameShell>
</template>

<style scoped>
/* The visible title is drawn with a globe; this text is what screen readers read. */
.geo-title__label {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}

.geo-title__globe {
  margin: 0 0.04em;
  color: var(--dz-primary-strong);
  font-size: 0.78em;
  vertical-align: 0.04em;
}

.geo-game__locked {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.geo-game__status {
  display: flex;
  justify-content: space-between;
  width: 100%;
  font-weight: 600;
}

.geo-game__help {
  margin: 0;
  color: var(--dz-text-muted);
  font-size: 0.875rem;
}

.geo-game__error {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  width: 100%;
  margin: 0;
  color: var(--dz-accent-strong);
  font-size: 0.95rem;
  font-weight: 600;
}

.geo-game__reveal {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  margin: 0;
  font-size: 1.1rem;
}

.geo-game__reveal strong {
  color: var(--dz-primary-strong);
  font-size: 1.75rem;
}

.geo-game__stage {
  position: relative;
  width: 100%;
}

.geo-game__layer {
  position: absolute;
  inset: 0;
  height: auto;
}

.geo-game__layer--hidden {
  visibility: hidden;
}

.geo-game__action {
  width: 100%;
  max-width: 24rem;
}

.geo-game__actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
  width: 100%;
  max-width: 32rem;
}
</style>
