<script setup>
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'
import { usePalpites } from '../composables/usePalpites.js'

const router = useRouter()
const { user } = useAuth()
const { meusAbertos, meusBloqueados, meusFinalizados, totalPalpites } = usePalpites()
</script>

<template>
  <div class="scroll-content">
    <div class="page-header">
      <h2 class="page-title">🎯 Meus Palpites</h2>
      <p class="page-subtitle">{{ user?.nome }} · {{ user?.pontos }} pts · {{ user?.exatos }} exato(s)</p>
    </div>

    <!-- Abertos para editar -->
    <div v-if="meusAbertos.length" class="section">
      <p class="section-title green">✏️ Abertos para editar</p>
      <div class="card-list">
        <div v-for="g in meusAbertos" :key="g.id" class="palpite-card">
          <div class="palpite-header">
            <span class="palpite-flag">{{ g.flagA }}</span>
            <span class="palpite-vs">{{ g.teamA }} × {{ g.teamB }}</span>
            <span class="palpite-flag">{{ g.flagB }}</span>
          </div>
          <div class="palpite-body">
            <div>
              <p class="palpite-label">Meu palpite</p>
              <p class="palpite-score green-text">{{ g.palpiteText }}</p>
            </div>
            <div class="palpite-right">
              <p class="palpite-date">{{ g.date }} · {{ g.time }}</p>
              <button class="btn-editar" @click="router.push('/jogos')">Editar</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Aguardando resultado -->
    <div v-if="meusBloqueados.length" class="section">
      <p class="section-title orange">⏳ Aguardando resultado</p>
      <div class="card-list">
        <div v-for="g in meusBloqueados" :key="g.id" class="palpite-card">
          <div class="palpite-header">
            <span class="palpite-flag">{{ g.flagA }}</span>
            <span class="palpite-vs">{{ g.teamA }} × {{ g.teamB }}</span>
            <span class="palpite-flag">{{ g.flagB }}</span>
            <span class="badge-blocked">🔒 Bloqueado</span>
          </div>
          <div class="palpite-body">
            <div>
              <p class="palpite-label">Meu palpite</p>
              <p class="palpite-score muted">{{ g.palpiteText }}</p>
            </div>
            <p class="palpite-date">{{ g.date }} · {{ g.time }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Finalizados -->
    <div v-if="meusFinalizados.length" class="section">
      <p class="section-title gray">✅ Finalizados</p>
      <div class="card-list">
        <div v-for="g in meusFinalizados" :key="g.id" class="palpite-card">
          <div class="palpite-header">
            <span class="palpite-flag">{{ g.flagA }}</span>
            <span class="palpite-vs">{{ g.teamA }} × {{ g.teamB }}</span>
            <span class="palpite-flag">{{ g.flagB }}</span>
          </div>
          <div class="result-block">
            <div class="result-item">
              <p class="palpite-label">Resultado</p>
              <p class="result-score">{{ g.resultadoText }}</p>
            </div>
            <div class="result-item">
              <p class="palpite-label">Meu palpite</p>
              <p class="my-score">{{ g.palpiteText }}</p>
            </div>
            <div class="result-pts" :style="{ color: g.pontosColor }">
              {{ g.pontosText }}
            </div>
          </div>
          <button class="btn-detalhes" @click="router.push(`/resultado/${g.id}`)">
            Ver quem cravou →
          </button>
        </div>
      </div>
    </div>

    <!-- Empty -->
    <div v-if="totalPalpites === 0" class="empty-state">
      <p class="empty-icon">🎯</p>
      <p class="empty-title">Você ainda não palpitou</p>
      <p class="empty-desc">Vá para Jogos e faça seus palpites antes dos apitos!</p>
      <button class="btn-ir" @click="router.push('/jogos')">Ver jogos →</button>
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
.page-header { padding: 22px 20px 0; }
.page-title { font-size: 26px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.5px; }
.page-subtitle { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }
.section { padding: 16px 20px 0; }
.section-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 10px;
}
.section-title.green { color: var(--accent-green); }
.section-title.orange { color: var(--accent-orange); }
.section-title.gray { color: var(--text-tertiary); }
.card-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.palpite-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  padding: 15px 16px;
}
.palpite-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.palpite-flag { font-size: 22px; }
.palpite-vs { font-size: 15px; font-weight: 700; color: var(--text-primary); flex: 1; }
.badge-blocked {
  font-size: 11px;
  color: var(--accent-orange);
  font-weight: 700;
  background: rgba(251,146,60,0.1);
  padding: 4px 10px;
  border-radius: 10px;
}
.palpite-body {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.palpite-label { font-size: 12px; color: var(--text-secondary); font-weight: 500; margin-bottom: 3px; }
.palpite-score { font-size: 28px; font-weight: 700; line-height: 1; letter-spacing: 1px; }
.palpite-score.green-text { color: var(--accent-green); }
.palpite-score.muted { color: var(--text-tertiary); }
.palpite-right { text-align: right; }
.palpite-date { font-size: 12px; color: var(--text-secondary); margin-bottom: 6px; }
.btn-editar {
  background: var(--accent-green-dim);
  color: var(--accent-green);
  border: 1px solid rgba(0,220,130,0.25);
  border-radius: 10px;
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 700;
  font-family: inherit;
}
.result-block {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--bg-card-hover);
  border-radius: 12px;
  padding: 12px 14px;
  margin-bottom: 10px;
}
.result-item { flex: 1; }
.result-score { font-size: 24px; font-weight: 700; color: var(--text-primary); line-height: 1; letter-spacing: 2px; }
.my-score { font-size: 20px; font-weight: 600; color: var(--text-tertiary); line-height: 1; }
.result-pts {
  font-size: 20px;
  font-weight: 700;
  text-align: center;
  background: rgba(0,0,0,0.2);
  border-radius: 10px;
  padding: 8px 12px;
  min-width: 52px;
}
.btn-detalhes {
  width: 100%;
  background: rgba(255,255,255,0.04);
  color: var(--text-secondary);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 10px;
  padding: 10px;
  font-size: 13px;
  font-weight: 600;
  font-family: inherit;
}
.empty-state { text-align: center; padding: 64px 24px; }
.empty-icon { font-size: 56px; margin-bottom: 18px; }
.empty-title { font-size: 20px; font-weight: 700; color: #B0B8C4; margin-bottom: 8px; }
.empty-desc { font-size: 14px; color: var(--text-secondary); margin-bottom: 28px; line-height: 1.5; }
.btn-ir {
  background: var(--accent-green);
  color: #060E1C;
  border-radius: 14px;
  padding: 15px 30px;
  font-size: 15px;
  font-weight: 700;
  font-family: inherit;
}
.spacer { height: 28px; }
</style>
