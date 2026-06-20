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

const COLORS = ['#F7C948', '#94A3B8', '#CD7F32', '#60A5FA', '#A78BFA', '#4ADE80', '#F87171']

// Generate mock guesses for each game (replace with real cross-participant data later)
function generateGuesses(game) {
  const names = ['Ricardo', 'Pajé', 'Big', 'Flávia', 'Mari Gallo', 'Mari Som', 'Lere']
  if (game.isFinalizado) {
    // Only show participants who had a palpite — use quemCravou + quemVencedor
    const all = [...(game.quemCravou || []), ...(game.quemVencedor || [])]
    if (all.length === 0) {
      // Fallback: show all with mock scores
      return names.map((n, i) => {
        const a = Math.floor(Math.random() * 4)
        const b = Math.floor(Math.random() * 4)
        return { name: n, initial: n[0], avatarBg: COLORS[i % COLORS.length], label: a + '-' + b, labelColor: '#2A3D52' }
      })
    }
    return all.map((n, i) => {
      const pIdx = names.indexOf(n)
      return { name: n, initial: n[0], avatarBg: COLORS[pIdx >= 0 ? pIdx % COLORS.length : i % COLORS.length], label: '✓', labelColor: '#EBF0F5' }
    })
  }
  // Non-finalized: show all participants
  return names.map((n, i) => {
    const a = Math.floor(Math.random() * 3)
    const b = Math.floor(Math.random() * 3)
    return { name: n, initial: n[0], avatarBg: COLORS[i % COLORS.length], label: a + '-' + b, labelColor: '#EBF0F5' }
  })
}

const proximosJogos = computed(() =>
  jogos.value.filter(g => !g.isFinalizado).map(g => ({
    ...g,
    statusBadge: g.isBloqueado ? '● Em andamento' : '● Aberto',
    statusColor: g.isBloqueado ? 'var(--accent-orange)' : 'var(--accent-green)',
    statusBg: g.isBloqueado ? 'rgba(251,146,60,0.12)' : 'rgba(0,220,130,0.1)',
    guesses: generateGuesses(g),
  }))
)

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

        <!-- Two-column layout -->
        <div class="dash-two-col">
          <!-- LEFT: Proximos jogos -->
          <div class="dash-col-left">
            <p class="dash-col-label">PRÓXIMOS JOGOS &amp; EM ANDAMENTO</p>
            <div class="dash-games-list">
              <div v-for="jogo in proximosJogos" :key="jogo.id" class="dash-game-card">
                <!-- Header row -->
                <div class="dash-game-header">
                  <span class="dash-game-badge" :style="{ color: jogo.statusColor, background: jogo.statusBg }">
                    {{ jogo.statusBadge }}
                  </span>
                  <span class="dash-game-grupo-btn">{{ jogo.grupo }}</span>
                  <span class="dash-game-date">{{ jogo.date }} · {{ jogo.time }}</span>
                </div>
                <!-- Teams -->
                <div class="dash-game-teams">
                  <div class="dash-game-team">
                    <span class="dash-game-flag">{{ jogo.flagA }}</span>
                    <span class="dash-game-team-name">{{ jogo.teamA }}</span>
                  </div>
                  <span class="dash-game-vs">×</span>
                  <div class="dash-game-team right">
                    <span class="dash-game-team-name">{{ jogo.teamB }}</span>
                    <span class="dash-game-flag">{{ jogo.flagB }}</span>
                  </div>
                </div>
                <!-- Guesses -->
                <div class="dash-game-guesses">
                  <span class="dash-guesses-label">Palpites</span>
                  <div v-for="g in jogo.guesses" :key="g.name" class="dash-guess-chip">
                    <div class="dash-guess-avatar" :style="{ background: g.avatarBg }">{{ g.initial }}</div>
                    <span class="dash-guess-score" :style="{ color: g.labelColor }">{{ g.label }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- RIGHT: Ranking sidebar -->
          <div class="dash-col-right">
            <p class="dash-col-label">🏆 RANKING</p>
            <div class="dash-ranking-box">
              <div
                v-for="(r, i) in rankingList"
                :key="r.id"
                class="dash-rank-row"
                @click="goToPlayer(r)"
              >
                <span class="dash-rank-pos">{{ r.posicao }}</span>
                <span class="dash-rank-medal">{{ r.medal }}</span>
                <div class="dash-rank-avatar" :style="{ background: r.avatarColor }">{{ r.initial }}</div>
                <div class="dash-rank-info">
                  <p class="dash-rank-name">{{ r.name }}</p>
                  <p class="dash-rank-exatos">{{ r.exatos }} exato(s)</p>
                </div>
                <div class="dash-rank-pts-block">
                  <p class="dash-rank-pts" :style="{ color: i < 3 ? ['#F7C948','#94A3B8','#CD7F32'][i] : 'var(--text-primary)' }">
                    {{ r.pontos }}
                  </p>
                  <p class="dash-rank-pts-label">pts</p>
                </div>
              </div>
            </div>

            <!-- Como pontuar -->
            <div class="dash-scoring-card">
              <p class="dash-scoring-title">Como pontuar</p>
              <div class="dash-scoring-rows">
                <div class="dash-scoring-row">
                  <span class="dash-scoring-icon">🎯</span>
                  <span class="dash-scoring-text"><strong class="green">+3</strong> placar exato</span>
                </div>
                <div class="dash-scoring-row">
                  <span class="dash-scoring-icon">✓</span>
                  <span class="dash-scoring-text"><strong class="blue">+1</strong> vencedor / empate</span>
                </div>
                <div class="dash-scoring-row">
                  <span class="dash-scoring-icon">✗</span>
                  <span class="dash-scoring-text"><strong class="red">0</strong> erro</span>
                </div>
              </div>
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

/* ─── Two-column layout ─── */
.dash-two-col {
  display: grid;
  grid-template-columns: 1fr 296px;
  gap: 28px;
  align-items: start;
}
.dash-col-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1.2px;
  margin-bottom: 14px;
}

/* ─── Games list ─── */
.dash-games-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.dash-game-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  overflow: hidden;
}
.dash-game-header {
  padding: 10px 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  background: #0A1628;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.dash-game-badge {
  font-size: 12px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 20px;
  flex-shrink: 0;
}
.dash-game-grupo-btn {
  font-size: 11px;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.07);
  padding: 3px 8px;
  border-radius: 5px;
  font-weight: 600;
  cursor: pointer;
}
.dash-game-date {
  margin-left: auto;
  font-size: 12px;
  color: var(--text-muted);
  flex-shrink: 0;
}
.dash-game-teams {
  padding: 14px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.dash-game-team {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}
.dash-game-team.right {
  justify-content: flex-end;
}
.dash-game-flag {
  font-size: 28px;
  line-height: 1;
  flex-shrink: 0;
}
.dash-game-team-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}
.dash-game-vs {
  font-size: 16px;
  font-weight: 700;
  color: #1E3A5F;
  flex-shrink: 0;
}
.dash-game-guesses {
  padding: 10px 14px;
  background: rgba(0, 0, 0, 0.22);
  border-top: 1px solid rgba(255, 255, 255, 0.04);
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.dash-guesses-label {
  font-size: 10px;
  font-weight: 700;
  color: #2A3D52;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-right: 6px;
  flex-shrink: 0;
}
.dash-guess-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 20px;
  padding: 3px 8px 3px 4px;
  flex-shrink: 0;
}
.dash-guess-avatar {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  font-weight: 700;
  color: #030B16;
  flex-shrink: 0;
}
.dash-guess-score {
  font-size: 12px;
  font-weight: 600;
  font-family: 'Fira Code', 'Courier New', monospace;
}

/* ─── Ranking sidebar ─── */
.dash-ranking-box {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  overflow: hidden;
  margin-bottom: 14px;
}
.dash-rank-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  cursor: pointer;
  transition: background 0.1s;
}
.dash-rank-row:hover {
  background: rgba(255, 255, 255, 0.03);
}
.dash-rank-row:last-child {
  border-bottom: none;
}
.dash-rank-pos {
  font-size: 12px;
  color: #2A3D52;
  font-weight: 700;
  width: 16px;
  text-align: right;
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}
.dash-rank-medal {
  font-size: 14px;
  width: 18px;
  text-align: center;
  flex-shrink: 0;
  line-height: 1;
}
.dash-rank-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #030B16;
  flex-shrink: 0;
}
.dash-rank-info {
  flex: 1;
  min-width: 0;
}
.dash-rank-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.dash-rank-exatos {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 1px;
}
.dash-rank-pts-block {
  text-align: right;
  flex-shrink: 0;
}
.dash-rank-pts {
  font-size: 16px;
  font-weight: 700;
  line-height: 1;
}
.dash-rank-pts-label {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 1px;
}

/* ─── Como pontuar ─── */
.dash-scoring-card {
  background: rgba(96, 165, 250, 0.06);
  border: 1px solid rgba(96, 165, 250, 0.13);
  border-radius: 10px;
  padding: 12px 14px;
}
.dash-scoring-title {
  font-size: 10px;
  font-weight: 700;
  color: var(--accent-blue);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 8px;
}
.dash-scoring-rows {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.dash-scoring-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.dash-scoring-icon {
  font-size: 13px;
  flex-shrink: 0;
}
.dash-scoring-text {
  font-size: 12px;
  color: var(--text-secondary);
}
.dash-scoring-text .green { color: var(--accent-green); }
.dash-scoring-text .blue { color: var(--accent-blue); }
.dash-scoring-text .red { color: var(--accent-red); }
</style>
