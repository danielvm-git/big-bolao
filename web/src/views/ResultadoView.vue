<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useJogos } from '../composables/useJogos.js'

const route = useRoute()
const router = useRouter()
const { getJogo } = useJogos()

const game = computed(() => getJogo(route.params.id))
</script>

<template>
  <div class="resultado-page" v-if="game">
    <!-- Header -->
    <div class="result-header">
      <button class="btn-back" @click="router.back()">←</button>
      <h3 class="result-title">{{ game.teamA }} × {{ game.teamB }}</h3>
    </div>

    <!-- Resultado card -->
    <div class="result-card">
      <p class="result-suptitle">Resultado Final</p>
      <div class="result-bigscore">
        <div class="result-team-block">
          <span class="result-team-flag">{{ game.flagA }}</span>
          <p class="result-team-name">{{ game.teamA }}</p>
        </div>
        <p class="result-bigscore-value">{{ game.resultadoText }}</p>
        <div class="result-team-block">
          <span class="result-team-flag">{{ game.flagB }}</span>
          <p class="result-team-name">{{ game.teamB }}</p>
        </div>
      </div>
    </div>

    <!-- Meu palpite -->
    <div v-if="game.hasPalpite" class="my-palpite-card">
      <p class="section-card-label">Meu palpite</p>
      <div class="my-palpite-body">
        <p class="my-palpite-score">{{ game.palpiteText }}</p>
        <p class="my-palpite-result" :style="{ color: game.pontosColor }">
          {{ game.exato ? '🎯 Cravou! +3 pontos' : game.pontosGanhos > 0 ? '✓ Acertou o vencedor! +1 ponto' : '✗ Não pontuou dessa vez' }}
        </p>
      </div>
    </div>

    <!-- Quem cravou -->
    <div v-if="game.quemCravou?.length" class="list-section">
      <p class="list-section-title green">🎯 Cravou o placar exato!</p>
      <div class="list-card">
        <div v-for="nome in game.quemCravou" :key="nome" class="list-row">
          <span class="list-icon">🎯</span>
          <p class="list-name">{{ nome }}</p>
        </div>
      </div>
    </div>

    <!-- Quem acertou vencedor -->
    <div v-if="game.quemVencedor?.length" class="list-section">
      <p class="list-section-title blue">✓ Acertou vencedor ou empate</p>
      <div class="list-card">
        <div v-for="nome in game.quemVencedor" :key="nome" class="list-row">
          <span class="list-icon check">✓</span>
          <p class="list-name">{{ nome }}</p>
        </div>
      </div>
    </div>

    <div class="btn-area">
      <button class="btn-ranking" @click="router.push('/ranking')">
        🏆 Ver Ranking completo
      </button>
    </div>
  </div>

  <div v-else class="not-found">
    <p>Jogo não encontrado</p>
    <button @click="router.push('/')">Voltar</button>
  </div>
</template>

<style scoped>
.resultado-page {
  padding-bottom: 40px;
}
.result-header {
  padding: 20px 20px 0;
  display: flex;
  align-items: center;
  gap: 14px;
}
.btn-back {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: rgba(255,255,255,0.08);
  color: var(--text-primary);
  font-size: 20px;
  font-family: inherit;
  flex-shrink: 0;
}
.result-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.3px;
}
.result-card {
  margin: 20px 20px 0;
  background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-card-hover) 100%);
  border: 1px solid rgba(255,255,255,0.09);
  border-radius: 22px;
  padding: 30px 24px;
  text-align: center;
  animation: fadeInUp 0.35s ease 0.05s both;
}
.result-suptitle {
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 16px;
}
.result-bigscore {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
}
.result-team-block { text-align: center; }
.result-team-flag { font-size: 44px; line-height: 1; }
.result-team-name {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 6px;
  font-weight: 500;
}
.result-bigscore-value {
  font-size: 56px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 6px;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}
.my-palpite-card {
  margin: 14px 20px 0;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 18px;
  padding: 20px 22px;
  animation: fadeInUp 0.35s ease 0.1s both;
}
.section-card-label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
}
.my-palpite-body {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}
.my-palpite-score {
  font-size: 40px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
  letter-spacing: 3px;
  font-variant-numeric: tabular-nums;
}
.my-palpite-result {
  font-size: 16px;
  font-weight: 700;
  line-height: 1.3;
  max-width: 180px;
  text-align: right;
}
.list-section {
  margin: 14px 20px 0;
  animation: fadeInUp 0.35s ease 0.15s both;
}
.list-section-title {
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 10px;
}
.list-section-title.green { color: var(--accent-green); }
.list-section-title.blue { color: var(--accent-blue); }
.list-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  overflow: hidden;
}
.list-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.list-row:last-child { border-bottom: none; }
.list-icon { font-size: 18px; }
.list-icon.check { color: var(--accent-blue); }
.list-name { font-size: 15px; font-weight: 600; color: var(--text-primary); }
.btn-area { padding: 20px 20px 0; animation: fadeInUp 0.35s ease 0.25s both; }
.btn-ranking {
  width: 100%;
  background: var(--accent-gold-dim);
  color: var(--accent-gold);
  border: 1px solid rgba(247,201,72,0.25);
  border-radius: 14px;
  padding: 16px;
  font-size: 16px;
  font-weight: 700;
  font-family: inherit;
  letter-spacing: -0.2px;
}
.not-found { text-align: center; padding: 40px; }
</style>
