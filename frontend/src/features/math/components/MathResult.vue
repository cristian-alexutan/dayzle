<!-- MathResult: the end-of-game dialog: score, how close, steps, difficulty, time, a solution. -->
<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import AppDialog from '@/shared/components/AppDialog.vue'
import ResultCard from '@/shared/components/ResultCard.vue'

import { MAX_SCORE, type MathGame } from '../types'
import StepList from './StepList.vue'

const props = defineProps<{ game: MathGame }>()
const visible = defineModel<boolean>('visible', { required: true })

const { t } = useI18n()

const title = computed(() => {
  const { solved, target, final_result, distance } = props.game
  if (solved) return t('math.result.exact', { target })
  return t('math.result.close', { result: final_result, distance, target })
})
const operations = computed(() => props.game.operations ?? props.game.steps.length)
</script>

<template>
  <AppDialog v-model:visible="visible" :header="title" :style="{ width: 'min(90vw, 24rem)' }">
    <ResultCard :result="String(game.score ?? 0)" :duration-ms="game.duration_ms">
      <p class="math-result__out-of" data-test="score-out-of">
        {{ t('math.result.outOf', { max: MAX_SCORE }) }}
      </p>
      <dl class="math-result__details">
        <div>
          <dt>{{ t('math.result.stepsLabel') }}</dt>
          <dd data-test="result-steps">
            {{
              t('math.result.steps', { count: operations, min: game.min_operations }, operations)
            }}
          </dd>
        </div>
        <div v-if="game.difficulty">
          <dt>{{ t('math.result.difficultyLabel') }}</dt>
          <dd data-test="result-difficulty">
            {{ t(`math.result.difficulty.${game.difficulty}`) }}
          </dd>
        </div>
      </dl>
      <section v-if="game.solution?.length" class="math-result__solution" data-test="solution">
        <h3 class="math-result__heading">{{ t('math.result.solution') }}</h3>
        <StepList :steps="game.solution" />
      </section>
    </ResultCard>
  </AppDialog>
</template>

<style scoped>
.math-result__out-of {
  margin: 0 0 1rem;
  color: var(--dz-text-muted);
}

.math-result__details {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  margin: 0 0 1rem;
}

.math-result__details dt {
  color: var(--dz-text-muted);
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.math-result__details dd {
  margin: 0.2rem 0 0;
  font-weight: 700;
}

.math-result__solution {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  text-align: left;
}

.math-result__heading {
  margin: 0;
  font-size: 1rem;
  font-weight: 800;
}
</style>
