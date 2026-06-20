<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useJogos } from '../composables/useJogos.js'
import { useRanking } from '../composables/useRanking.js'

const router = useRouter()
const { jogos, loaded: jogosLoaded } = useJogos()
const { rankingList } = useRanking()

const page = ref('landing')
const showBreadcrumb = computed(() => page.value !== 'landing')

const finalizadoCount = computed(() => jogos.value.filter(g => g.isFinalizado).length)
const totalGames = computed(() => jogos.value.length)
const abertoCount = computed(() => jogos.value.filter(g => g.isAberto).length)
const totalPlayers = computed(() => rankingList.value.length)

const leader = computed(() => rankingList.value[0] || null)

function goHome() {
  page.value = 'landing'
}

function goBack() {
  page.value = 'landing'
}

function goToPlayer(player) {
  // Will navigate to player detail view in e03-s05
  console.log('Player:', player)
}
</script>

<template>
  <div class="dashboard">
    <!-- STICKY HEADER -->
    <header class="dash-header">
      <div class="dash-header-inner">
        <div class="dash-brand" @click="goHome">
          <span class="dash-logo">⚽</span>
          <span class="dash-name">Big Bolão</span>
          <span class="dash-badge">COPA 2026</span>
        </div>
        <div class="dash-header-spacer" />
        <button v-if="showBreadcrumb" class="dash-back-btn" @click="goBack">
          ← Voltar
        </button>
        <div class="dash-progress">
          <span class="dash-progress-dot" />
          <span class="dash-progress-text">
            <span class="dash-progress-count">{{ finalizadoCount }}</span>
            <span class="dash-progress-sep">/</span>
            <span class="dash-progress-total">{{ totalGames }}</span>
            <span class="dash-progress-label"> jogos finalizados</span>
          </span>
        </div>
      </div>
    </header>

    <!-- MAIN CONTENT -->
    <main class="dash-main">
      <!-- LANDING -->
      <div v-if="page === 'landing'" class="dash-landing">
        <!-- Hero -->
        <div class="dash-hero">
          <div>
            <h1 class="dash-hero-title">Bolão da Copa 2026</h1>
            <p class="dash-hero-subtitle">
              {{ totalPlayers }} participantes · {{ finalizadoCount }} jogos finalizados · {{ abertoCount }} abertos para palpitar
            </p>
          </div>
          <div v-if="leader" class="dash-leader-card" @click="goToPlayer(leader)">
            <span class="dash-leader-icon">🏆</span>
            <div>
              <p class="dash-leader-label">Líder atual</p>
              <p class="dash-leader-name">{{ leader.name }} · {{ leader.pontos }} pts</p>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: var(--bg-deep);
  color: var(--text-primary);
  animation: fadeIn 0.2s ease;
}

/* ─── Sticky Header ─── */
.dash-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(3, 11, 22, 0.96);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-subtle);
}
.dash-header-inner {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 32px;
  height: 54px;
  display: flex;
  align-items: center;
  gap: 16px;
}
.dash-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  flex-shrink: 0;
}
.dash-logo {
  font-size: 22px;
  line-height: 1;
}
.dash-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.3px;
}
.dash-badge {
  font-size: 11px;
  font-weight: 700;
  color: var(--accent-gold);
  letter-spacing: 1.2px;
  background: rgba(247, 201, 72, 0.12);
  padding: 2px 9px;
  border-radius: 20px;
}
.dash-header-spacer {
  flex: 1;
}
.dash-back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-tertiary);
  padding: 6px 14px;
  border-radius: 8px;
  font-family: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}
.dash-progress {
  display: flex;
  align-items: center;
  gap: 7px;
  flex-shrink: 0;
}
.dash-progress-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent-green);
  display: inline-block;
}
.dash-progress-text {
  font-size: 13px;
  color: var(--text-muted);
}
.dash-progress-count {
  color: var(--text-tertiary);
  font-weight: 600;
}
.dash-progress-sep {
  color: var(--text-muted);
}
.dash-progress-total {
  color: var(--text-tertiary);
}
.dash-progress-label {
  color: var(--text-muted);
}

/* ─── Main Content ─── */
.dash-main {
  max-width: 1440px;
  margin: 0 auto;
  padding: 36px 32px;
}
.dash-landing {
  animation: fadeInUp 0.3s ease;
}

/* ─── Hero ─── */
.dash-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 28px;
  flex-wrap: wrap;
}
.dash-hero-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.7px;
}
.dash-hero-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 5px;
}
.dash-leader-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(247, 201, 72, 0.08);
  border: 1px solid rgba(247, 201, 72, 0.18);
  border-radius: 12px;
  padding: 10px 18px;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s;
}
.dash-leader-card:hover {
  background: rgba(247, 201, 72, 0.14);
}
.dash-leader-icon {
  font-size: 20px;
}
.dash-leader-label {
  font-size: 10px;
  font-weight: 700;
  color: var(--accent-gold);
  text-transform: uppercase;
  letter-spacing: 1.2px;
  margin-bottom: 3px;
}
.dash-leader-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
}
</style>
