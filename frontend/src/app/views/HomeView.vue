<!-- HomeView: Landing page displaying cards for the five daily puzzle games. -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import AppCard from '@/shared/components/AppCard.vue'

interface GameItem {
  key: 'word' | 'logic' | 'math' | 'trivia' | 'geo'
  path: string
  icon: string
}

const GAMES: readonly GameItem[] = [
  { key: 'word', path: '/games/word', icon: 'pi pi-align-left' },
  { key: 'logic', path: '/games/logic', icon: 'pi pi-sun' },
  { key: 'math', path: '/games/math', icon: 'pi pi-calculator' },
  { key: 'trivia', path: '/games/trivia', icon: 'pi pi-question-circle' },
  { key: 'geo', path: '/games/geo', icon: 'pi pi-map-marker' },
]

const { t } = useI18n()
</script>

<template>
  <main class="home-page" data-test="home-page">
    <section class="home-page__hero">
      <h1 class="home-page__title" data-test="home-title">{{ t('home.title') }}</h1>
      <p class="home-page__subtitle">{{ t('home.subtitle') }}</p>
    </section>

    <section class="home-page__grid" :aria-label="t('home.title')">
      <AppCard
        v-for="game in GAMES"
        :key="game.key"
        class="game-card"
        :data-test="`game-card-${game.key}`"
      >
        <template #title>
          <div class="game-card__header">
            <span class="game-card__icon" aria-hidden="true">
              <i :class="game.icon" />
            </span>
            <RouterLink
              :to="game.path"
              class="game-card__title-link"
              :data-test="`game-link-${game.key}`"
            >
              {{ t(`home.games.${game.key}.title`) }}
            </RouterLink>
          </div>
        </template>

        <template #content>
          <p class="game-card__description" :data-test="`game-description-${game.key}`">
            {{ t(`home.games.${game.key}.description`) }}
          </p>
        </template>

        <template #footer>
          <div class="game-card__footer">
            <RouterLink
              :to="game.path"
              class="game-card__play-link"
              :data-test="`game-play-${game.key}`"
            >
              <i class="pi pi-play" aria-hidden="true" />
              <span>{{ t('home.play') }}</span>
            </RouterLink>
          </div>
        </template>
      </AppCard>
    </section>
  </main>
</template>

<style scoped>
.home-page {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  max-width: 64rem;
  margin: 0 auto;
  padding: 1.5rem 1rem 3rem;
}

.home-page__hero {
  text-align: center;
}

.home-page__title {
  margin: 0 0 0.5rem;
  font-size: 2.25rem;
  font-weight: 800;
  letter-spacing: 0.01em;
  color: var(--dz-text);
}

.home-page__subtitle {
  margin: 0 auto;
  max-width: 36rem;
  font-size: 1.05rem;
  color: var(--dz-text-muted);
}

.home-page__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(17.5rem, 1fr));
  gap: 1.25rem;
}

.game-card {
  display: flex;
  flex-direction: column;
  height: 100%;
  border: 1px solid var(--dz-border);
  background: var(--dz-surface);
  transition:
    transform 0.15s ease,
    border-color 0.15s ease;
}

.game-card :deep(.p-card-body) {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.game-card :deep(.p-card-content) {
  flex: 1;
}

.game-card:hover {
  transform: translateY(-2px);
  border-color: var(--dz-border-strong);
}

.game-card__header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.game-card__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.75rem;
  background: var(--dz-primary);
  color: var(--dz-on-primary);
  font-size: 1.2rem;
  flex-shrink: 0;
}

.game-card__title-link {
  color: var(--dz-text);
  text-decoration: none;
  font-size: 1.25rem;
  font-weight: 700;
}

.game-card__title-link:hover {
  text-decoration: underline;
}

.game-card__description {
  margin: 0;
  color: var(--dz-text-muted);
  line-height: 1.5;
}

.game-card__footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 0.25rem;
}

.game-card__play-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 9999px;
  background: var(--dz-primary);
  color: var(--dz-on-primary);
  font-size: 0.95rem;
  font-weight: 700;
  text-decoration: none;
  transition: background-color 0.15s ease;
}

.game-card__play-link:hover {
  background: var(--dz-primary-strong);
}
</style>
