<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'
import { useJogos } from '../composables/useJogos.js'
import { useRanking } from '../composables/useRanking.js'
import { REGRA_PONTUACAO } from '../data/mock.js'
import PalpiteModal from '../components/PalpiteModal.vue'

const router = useRouter()
const { user } = useAuth()
const { proximoJogo, semPalpiteCount, loaded: jogosLoaded } = useJogos()
const { rankingList, top3, loaded: rankingLoaded } = useRanking()

const myRank = computed(() => rankingList.value.find(p => p.isMe))
const myPosicao = computed(() => myRank.value?.posicao || '-')
const myPontos = computed(() => myRank.value?.pontos || 0)
const myExatos = computed(() => myRank.value?.exatos || 0)

const palpiteTarget = ref(null)
const showModal = ref(false)

function openPalpite(game) {
  palpiteTarget.value = game
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  palpiteTarget.value = null
}

function onSaved() {
  closeModal()
}
</script>

<template>
  <div class="scroll-content">
    <!-- Header -->
    <div class="home-header">
      <div>
        <p class="home-label">⚽ Big Bolão · Copa 2026</p>
        <h2 class="home-greeting">Oi, {{ user?.nome }}! 👋</h2>
      </div>
      <div class="home-avatar">{{ user?.nome?.[0] || '?' }}</div>
    </div>

    <!-- Stats card -->
    <div class="stats-card">
      <div class="stat-block">
        <p class="stat-value gold">#{{ myPosicao }}</p>
        <p class="stat-label">Posição</p>
      </div>
      <div class="stat-block">
        <p class="stat-value white">{{ myPontos }}</p>
        <p class="stat-label">Pontos</p>
      </div>
      <div class="stat-block no-border">
        <p class="stat-value green">{{ myExatos }}</p>
        <p class="stat-label">Exatos 🎯</p>
      </div>
    </div>

    <!-- Proximo jogo -->
    <div v-if="proximoJogo" class="next-game-section">
      <p class="section-label">Próximo jogo para palpitar</p>
      <div class="next-game-card">
        <div class="next-teams">
          <div class="next-team-block">
            <span class="next-flag">{{ proximoJogo.flagA }}</span>
            <span class="next-team-name">{{ proximoJogo.teamA }}</span>
          </div>
          <div class="next-team-block">
            <span class="next-team-name">{{ proximoJogo.teamB }}</span>
            <span class="next-flag">{{ proximoJogo.flagB }}</span>
          </div>
        </div>
        <p class="next-date">{{ proximoJogo.date }} · {{ proximoJogo.time }} · {{ proximoJogo.grupo }}</p>
        <button class="btn-palpitar-now" @click="openPalpite(proximoJogo)">Palpitar agora →</button>
      </div>
    </div>

    <!-- Sem palpite count -->
    <div v-if="semPalpiteCount > 0" class="reminder-banner">
      📋 Você ainda tem <strong>{{ semPalpiteCount }} jogo(s)</strong> para palpitar
    </div>

    <div v-if="semPalpiteCount === 0 && proximoJogo" class="all-done-banner">
      🎉 Você palpitou em todos os jogos abertos!
    </div>

    <!-- Mini ranking -->
    <div class="mini-ranking">
      <div class="section-header">
        <p class="section-label">🏆 Top 3 agora</p>
        <button class="link-all" @click="router.push('/ranking')">Ver tudo →</button>
      </div>
      <div class="mini-ranking-list">
        <div
          v-for="(p, i) in top3"
          :key="p.id"
          class="mini-rank-row"
          :class="{ 'is-me': p.isMe }"
        >
          <span class="mini-medal">{{ p.medal }}</span>
          <div
            class="mini-avatar"
            :style="{ background: p.avatarColor }"
          >{{ p.initial }}</div>
          <div class="mini-info">
            <p class="mini-name">{{ p.name }}</p>
            <p class="mini-exatos">{{ p.exatos }} exato(s)</p>
          </div>
          <p class="mini-pontos">
            {{ p.pontos }}<span class="mini-pts"> pts</span>
          </p>
        </div>
      </div>
    </div>

    <!-- Share card -->
    <div class="share-card">
      <div>
        <p class="share-title">📲 Convidar amigos</p>
        <p class="share-desc">Compartilhe o link do bolão</p>
      </div>
      <button class="share-btn">Compartilhar</button>
    </div>

    <div class="spacer" />
  </div>

  <PalpiteModal
    v-if="showModal && palpiteTarget"
    :game="palpiteTarget"
    @close="closeModal"
    @saved="onSaved"
  />
</template>

<style scoped>
.scroll-content {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}
.home-header {
  padding: 22px 20px 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.home-label {
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
}
.home-greeting {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
  margin-top: 3px;
  letter-spacing: -0.5px;
}
.home-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #60A5FA, #A78BFA);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
  color: white;
  box-shadow: 0 0 12px rgba(96,165,250,0.25);
}
.stats-card {
  margin: 16px 20px 0;
  background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-surface-light) 100%);
  border: 1px solid var(--border-subtle);
  border-radius: 18px;
  padding: 22px;
  display: flex;
  animation: fadeInUp 0.4s ease 0.05s both;
}
.stat-block {
  flex: 1;
  text-align: center;
  padding-right: 16px;
  border-right: 1px solid rgba(255,255,255,0.06);
}
.stat-block.no-border { border: none; padding-left: 16px; padding-right: 0; }
.stat-block:not(:first-child):not(.no-border) { padding-left: 16px; }
.stat-value { font-size: 32px; font-weight: 700; line-height: 1; }
.stat-value.gold { color: var(--accent-gold); }
.stat-value.white { color: var(--text-primary); }
.stat-value.green { color: var(--accent-green); }
.stat-label { font-size: 12px; color: var(--text-secondary); margin-top: 4px; font-weight: 500; }
.section-label {
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 10px;
}
.next-game-section {
  margin: 16px 20px 0;
  animation: fadeInUp 0.4s ease 0.1s both;
}
.next-game-card {
  background: var(--bg-card);
  border: 1px solid var(--border-green);
  border-radius: 18px;
  padding: 18px 20px;
}
.next-teams { display: flex; justify-content: space-between; margin-bottom: 14px; }
.next-team-block { display: flex; align-items: center; gap: 10px; }
.next-flag { font-size: 32px; }
.next-team-name { font-size: 17px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.3px; }
.next-date {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 14px;
}
.btn-palpitar-now {
  width: 100%;
  background: var(--accent-green);
  color: #060E1C;
  border-radius: 12px;
  padding: 15px;
  font-size: 15px;
  font-weight: 700;
  font-family: inherit;
  letter-spacing: -0.2px;
}
.reminder-banner {
  margin: 10px 20px 0;
  padding: 10px 14px;
  background: rgba(96,165,250,0.07);
  border-radius: 10px;
  border: 1px solid rgba(96,165,250,0.12);
  font-size: 13px;
  color: var(--text-secondary);
}
.all-done-banner {
  margin: 16px 20px 0;
  background: rgba(0,220,130,0.08);
  border: 1px solid rgba(0,220,130,0.2);
  border-radius: 14px;
  padding: 16px;
  font-size: 14px;
  color: var(--accent-green);
  font-weight: 600;
}
.mini-ranking {
  margin: 20px 20px 0;
  animation: fadeInUp 0.4s ease 0.15s both;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.section-header .section-label { margin-bottom: 0; }
.link-all {
  background: none;
  border: none;
  color: var(--accent-green);
  font-size: 13px;
  font-weight: 600;
  font-family: inherit;
}
.mini-ranking-list {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  overflow: hidden;
}
.mini-rank-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.mini-rank-row:last-child { border-bottom: none; }
.mini-rank-row.is-me { background: rgba(0,220,130,0.07); }
.mini-medal { font-size: 22px; width: 28px; text-align: center; }
.mini-avatar {
  width: 38px; height: 38px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 700;
  color: #060E1C;
  flex-shrink: 0;
}
.mini-info { flex: 1; }
.mini-name { font-size: 15px; font-weight: 600; color: var(--text-primary); }
.mini-exatos { font-size: 12px; color: var(--text-secondary); margin-top: 1px; }
.mini-pontos { font-size: 20px; font-weight: 700; color: var(--accent-gold); }
.mini-pts { font-size: 13px; color: var(--text-secondary); font-weight: 500; }
.share-card {
  margin: 14px 20px 28px;
  background: linear-gradient(135deg, #0B1F3C, #0E2B50);
  border: 1px solid rgba(96,165,250,0.2);
  border-radius: 16px;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  animation: fadeInUp 0.4s ease 0.2s both;
}
.share-title { font-size: 15px; font-weight: 700; color: var(--text-primary); }
.share-desc { font-size: 13px; color: var(--text-secondary); margin-top: 3px; }
.share-btn {
  background: var(--accent-blue);
  color: #030B16;
  border: none;
  border-radius: 10px;
  padding: 10px 18px;
  font-size: 14px;
  font-weight: 700;
  white-space: nowrap;
  font-family: inherit;
  flex-shrink: 0;
}
.spacer { height: 20px; }
</style>
