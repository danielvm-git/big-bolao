<script setup>
import { useRouter } from 'vue-router'

const props = defineProps({
  game: { type: Object, required: true },
})

const emit = defineEmits(['palpitar'])
const router = useRouter()

function handleAction() {
  if (props.game.isFinalizado) {
    router.push(`/resultado/${props.game.id}`)
  } else if (props.game.isAberto) {
    emit('palpitar', props.game)
  }
}
</script>

<template>
  <div class="game-card">
    <!-- Badge row -->
    <div class="card-header">
      <span class="card-grupo">{{ game.grupo }}</span>
      <span
        class="card-badge"
        :style="{ background: game.statusBg, color: game.statusColor }"
      >{{ game.statusLabel }}</span>
    </div>

    <!-- Teams -->
    <div class="card-teams">
      <div class="team-block left">
        <span class="team-flag">{{ game.flagA }}</span>
        <span class="team-name">{{ game.teamA }}</span>
      </div>
      <span class="team-vs">×</span>
      <div class="team-block right">
        <span class="team-flag">{{ game.flagB }}</span>
        <span class="team-name">{{ game.teamB }}</span>
      </div>
    </div>

    <!-- Date/time -->
    <p class="card-date">📅 {{ game.date }} · {{ game.time }}</p>

    <!-- Resultado row (finalizado) -->
    <div v-if="game.isFinalizado" class="result-row">
      <div class="result-block">
        <div class="result-section">
          <p class="result-label">Resultado</p>
          <p class="result-score">{{ game.resultadoText }}</p>
        </div>
        <div v-if="game.hasPalpite" class="result-section">
          <p class="result-label">Meu palpite</p>
          <p class="result-palpite">{{ game.palpiteText }}</p>
        </div>
        <div v-if="game.hasPalpite" class="result-points" :style="{ color: game.pontosColor }">
          {{ game.pontosText }}
        </div>
      </div>
    </div>

    <!-- Palpite salvo (aberto com palpite) -->
    <p v-else-if="game.isAbertoComPalpite" class="saved-palpite">
      ✓ Meu palpite: <strong>{{ game.palpiteText }}</strong>
    </p>

    <!-- Bloqueado com palpite -->
    <p v-else-if="game.isBloqueadoComPalpite" class="blocked-palpite">
      🔒 Meu palpite: <strong>{{ game.palpiteText }}</strong>
    </p>

    <!-- Actions -->
    <div class="card-actions">
      <button
        v-if="game.isAberto"
        class="btn-palpitar"
        :class="{ 'btn-edit': game.hasPalpite }"
        @click="emit('palpitar', game)"
      >
        {{ game.hasPalpite ? '✏️ Editar palpite' : '+ Palpitar' }}
      </button>
      <button
        v-if="game.isFinalizado"
        class="btn-detalhes"
        @click="router.push(`/resultado/${game.id}`)"
      >
        Ver detalhes →
      </button>
      <div v-if="game.isBloqueado" class="blocked-badge">
        🔒 Em andamento
      </div>
    </div>
  </div>
</template>

<style scoped>
.game-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 18px;
  padding: 16px;
  animation: fadeInUp 0.3s ease;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.card-grupo {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}
.card-badge {
  font-size: 12px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 22px;
  letter-spacing: 0.2px;
}
.card-teams {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}
.team-block {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
}
.team-block.left { justify-content: flex-start; }
.team-block.right { justify-content: flex-end; }
.team-flag { font-size: 34px; line-height: 1; }
.team-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}
.team-vs {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 700;
  padding: 0 6px;
}
.card-date {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 10px;
}
.result-row {
  background: var(--bg-card-hover);
  border-radius: 12px;
  padding: 12px 14px;
  margin-bottom: 10px;
}
.result-block {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}
.result-section { flex: 1; }
.result-label {
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 3px;
}
.result-score {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
  letter-spacing: 2px;
}
.result-palpite {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-tertiary);
}
.result-points {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 700;
  background: rgba(0,0,0,0.25);
  border-radius: 10px;
  padding: 8px 14px;
  min-width: 56px;
  justify-content: center;
}
.saved-palpite {
  font-size: 13px;
  color: var(--accent-green);
  margin-bottom: 10px;
  font-weight: 500;
}
.saved-palpite strong { font-weight: 700; }
.blocked-palpite {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 10px;
}
.blocked-palpite strong {
  color: #B0B8C4;
  font-weight: 600;
}
.card-actions {
  display: flex;
  gap: 8px;
}
.btn-palpitar {
  flex: 1;
  background: var(--accent-green);
  color: #060E1C;
  border-radius: 12px;
  padding: 13px;
  font-size: 14px;
  font-weight: 700;
  font-family: inherit;
  transition: all 0.12s;
}
.btn-edit {
  background: rgba(0,220,130,0.1);
  color: var(--accent-green);
  border: 1px solid rgba(0,220,130,0.22);
}
.btn-detalhes {
  flex: 1;
  background: rgba(255,255,255,0.05);
  color: var(--text-tertiary);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 13px;
  font-size: 14px;
  font-weight: 600;
  font-family: inherit;
}
.blocked-badge {
  flex: 1;
  background: rgba(251,146,60,0.08);
  border: 1px solid rgba(251,146,60,0.15);
  border-radius: 12px;
  padding: 13px;
  text-align: center;
  font-size: 13px;
  color: var(--accent-orange);
  font-weight: 600;
}
</style>
