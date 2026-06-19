<script setup>
import { useRouter } from 'vue-router'
import { useRanking } from '../composables/useRanking.js'
import { REGRA_PONTUACAO } from '../data/mock.js'

const router = useRouter()
const { rankingList, podium } = useRanking()

const CORES_AVATAR = ['#F7C948', '#94A3B8', '#CD7F32', '#60A5FA', '#A78BFA', '#4ADE80', '#F87171']

const blanks = [
  { name: '?', initial: '?', pontos: 0 },
  { name: '?', initial: '?', pontos: 0 },
  { name: '?', initial: '?', pontos: 0 },
]
</script>

<template>
  <div class="scroll-content">
    <div class="page-header">
      <h2 class="page-title">🏆 Ranking</h2>
      <p class="page-subtitle">🕐 Última atualização: agora há pouco</p>
    </div>

    <!-- Podium -->
    <div class="podium">
      <!-- 2nd -->
      <div class="podium-item silver">
        <div class="podium-avatar" style="background: #5C7A96;">
          {{ podium[0]?.initial || '?' }}
        </div>
        <p class="podium-name">{{ podium[0]?.name || '' }}</p>
        <p class="podium-pontos silver-text">{{ podium[0]?.pontos || 0 }} pts</p>
        <div class="podium-base silver-base">🥈</div>
      </div>
      <!-- 1st -->
      <div class="podium-item gold">
        <div class="podium-avatar first" style="background: linear-gradient(135deg, #F7C948, #F59E0B);">
          {{ podium[1]?.initial || '?' }}
        </div>
        <p class="podium-name">{{ podium[1]?.name || '' }}</p>
        <p class="podium-pontos gold-text">{{ podium[1]?.pontos || 0 }} pts</p>
        <div class="podium-base gold-base">🥇</div>
      </div>
      <!-- 3rd -->
      <div class="podium-item bronze">
        <div class="podium-avatar" style="background: #7A5C3F; border-color: #CD7F32;">
          {{ podium[2]?.initial || '?' }}
        </div>
        <p class="podium-name">{{ podium[2]?.name || '' }}</p>
        <p class="podium-pontos bronze-text">{{ podium[2]?.pontos || 0 }} pts</p>
        <div class="podium-base bronze-base">🥉</div>
      </div>
    </div>

    <!-- Full table -->
    <div class="ranking-table">
      <div
        v-for="p in rankingList"
        :key="p.id"
        class="rank-row"
        :style="{ background: p.meRowBg }"
      >
        <span class="rank-pos">{{ p.posicao }}</span>
        <span class="rank-medal">{{ p.medal }}</span>
        <div class="rank-avatar" :style="{ background: p.avatarColor }">{{ p.initial }}</div>
        <div class="rank-info">
          <p class="rank-name">{{ p.name }}</p>
          <span v-if="p.isMe" class="rank-you">Você</span>
        </div>
        <div class="rank-points">
          <p class="rank-pontos">{{ p.pontos }}</p>
          <p class="rank-exatos">{{ p.exatos }} exato(s)</p>
        </div>
      </div>
    </div>

    <!-- Regra -->
    <div class="regra-card">
      <p class="regra-title">ℹ️ Como pontuar</p>
      <p class="regra-text">🎯 3 pts — placar exato &nbsp;·&nbsp; ✓ 1 pt — vencedor ou empate &nbsp;·&nbsp; ✗ 0 pts — erro</p>
    </div>

    <div class="spacer" />
  </div>
</template>

<style scoped>
.scroll-content {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}
.page-header {
  padding: 22px 20px 0;
}
.page-title {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}
.page-subtitle {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}
.podium {
  padding: 24px 20px 0;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 10px;
}
.podium-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.podium-avatar {
  width: 48px; height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
  color: white;
  border: 2px solid transparent;
}
.podium-avatar.first {
  width: 68px; height: 68px;
  font-size: 26px;
  border: 3px solid #F7C948;
  box-shadow: 0 0 24px rgba(247,201,72,0.45);
}
.podium-name { font-size: 13px; font-weight: 700; color: var(--text-primary); text-align: center; line-height: 1.2; }
.podium-pontos { font-size: 14px; font-weight: 700; }
.silver-text { color: var(--text-tertiary); }
.gold-text { font-size: 17px; color: var(--accent-gold); }
.bronze-text { color: #CD7F32; }
.podium-base {
  width: 100%;
  border-radius: 10px 10px 0 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}
.gold-base {
  height: 86px;
  background: linear-gradient(180deg, rgba(247,201,72,0.22) 0%, rgba(247,201,72,0.06) 100%);
  font-size: 30px;
}
.silver-base {
  height: 62px;
  background: linear-gradient(180deg, rgba(148,163,184,0.2) 0%, rgba(148,163,184,0.06) 100%);
  font-size: 26px;
}
.bronze-base {
  height: 42px;
  background: linear-gradient(180deg, rgba(205,127,50,0.18) 0%, rgba(205,127,50,0.05) 100%);
}
.ranking-table {
  margin: 20px 20px 0;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 18px;
  overflow: hidden;
}
.rank-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.rank-row:last-child { border-bottom: none; }
.rank-pos {
  font-size: 14px;
  width: 22px;
  text-align: center;
  color: var(--text-secondary);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.rank-medal { font-size: 20px; width: 26px; text-align: center; }
.rank-avatar {
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
.rank-info { flex: 1; display: flex; align-items: center; gap: 8px; }
.rank-name { font-size: 15px; font-weight: 400; color: var(--text-primary); }
.rank-you {
  font-size: 11px;
  color: var(--accent-green);
  font-weight: 700;
  background: rgba(0,220,130,0.12);
  padding: 2px 8px;
  border-radius: 10px;
}
.rank-points { text-align: right; }
.rank-pontos { font-size: 18px; font-weight: 700; color: var(--text-primary); line-height: 1; }
.rank-exatos { font-size: 11px; color: var(--text-secondary); margin-top: 2px; }
.regra-card {
  margin: 12px 20px 28px;
  background: var(--accent-blue-dim);
  border: 1px solid rgba(96,165,250,0.18);
  border-radius: 12px;
  padding: 13px 16px;
}
.regra-title {
  font-size: 12px;
  color: var(--accent-blue);
  font-weight: 700;
  margin-bottom: 4px;
}
.regra-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}
.spacer { height: 20px; }
</style>
