<script setup>
import { ref, computed } from 'vue'
import { useJogos } from '../composables/useJogos.js'

const props = defineProps({
  game: { type: Object, required: true },
})
const emit = defineEmits(['close', 'saved'])

const { salvarPalpite } = useJogos()

const goalsA = ref(props.game.palpite?.goalsA ?? 0)
const goalsB = ref(props.game.palpite?.goalsB ?? 0)
const saved = ref(false)

const quickScores = [
  { a: 0, b: 0 }, { a: 1, b: 0 }, { a: 0, b: 1 },
  { a: 1, b: 1 }, { a: 2, b: 1 }, { a: 2, b: 0 },
]

function selectQuick(a, b) {
  goalsA.value = a
  goalsB.value = b
}

function handleSave() {
  salvarPalpite(props.game.id, goalsA.value, goalsB.value)
  saved.value = true
  setTimeout(() => {
    saved.value = false
    emit('saved')
  }, 1900)
}
</script>

<template>
  <Teleport to="body">
    <div class="modal-overlay" @click.self="emit('close')">
      <div class="modal-sheet">
        <div class="drag-handle" />

        <!-- Header -->
        <div class="modal-header">
          <h3 class="modal-title">Fazer palpite</h3>
          <button class="btn-close" @click="emit('close')">×</button>
        </div>

        <!-- Game info -->
        <div class="game-info">
          <div class="game-info-teams">
            <span class="gi-flag">{{ game.flagA }}</span>
            <span class="gi-name">{{ game.teamA }}</span>
            <span class="gi-vs">×</span>
            <span class="gi-name">{{ game.teamB }}</span>
            <span class="gi-flag">{{ game.flagB }}</span>
          </div>
          <p class="gi-deadline">{{ game.date }} · {{ game.time }} · Você pode editar até o apito inicial</p>
        </div>

        <!-- Success state -->
        <div v-if="saved" class="success-state">
          <p class="success-icon">✅</p>
          <p class="success-title">Palpite salvo!</p>
          <p class="success-sub">Dá pra editar até o jogo começar.</p>
        </div>

        <!-- Score selector -->
        <div v-else class="score-section">
          <div class="score-picker">
            <div class="score-team">
              <p class="score-team-name">{{ game.teamA }}</p>
              <div class="score-controls">
                <button class="score-btn" @click="goalsA = Math.max(0, goalsA - 1)">−</button>
                <span class="score-value">{{ goalsA }}</span>
                <button class="score-btn" @click="goalsA++">+</button>
              </div>
            </div>
            <div class="score-divider">×</div>
            <div class="score-team">
              <p class="score-team-name">{{ game.teamB }}</p>
              <div class="score-controls">
                <button class="score-btn" @click="goalsB = Math.max(0, goalsB - 1)">−</button>
                <span class="score-value">{{ goalsB }}</span>
                <button class="score-btn" @click="goalsB++">+</button>
              </div>
            </div>
          </div>

          <!-- Quick scores -->
          <p class="qs-label">Placares comuns</p>
          <div class="qs-grid">
            <button
              v-for="qs in quickScores"
              :key="`${qs.a}-${qs.b}`"
              class="qs-btn"
              :class="{ active: goalsA === qs.a && goalsB === qs.b }"
              @click="selectQuick(qs.a, qs.b)"
            >{{ qs.a }} × {{ qs.b }}</button>
          </div>

          <button class="btn-save" @click="handleSave">Salvar palpite</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  background: rgba(0,0,0,0.72);
  animation: fadeIn 200ms ease;
}
.modal-sheet {
  width: 100%;
  max-width: 430px;
  background: var(--bg-card);
  border-radius: 24px 24px 0 0;
  padding: 0 0 44px;
  animation: slideUp 280ms cubic-bezier(0.32,0.72,0,1);
  max-height: 92vh;
  overflow-y: auto;
}
.drag-handle {
  display: flex;
  justify-content: center;
  padding: 14px 0 0;
}
.drag-handle::after {
  content: '';
  width: 38px;
  height: 4px;
  background: rgba(255,255,255,0.14);
  border-radius: 2px;
}
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px 0;
}
.modal-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.3px;
}
.btn-close {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: rgba(255,255,255,0.07);
  color: var(--text-secondary);
  font-size: 18px;
  font-family: inherit;
  line-height: 1;
}
.game-info {
  padding: 12px 24px 16px;
  border-bottom: 1px solid var(--border-subtle);
}
.game-info-teams {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 6px;
}
.gi-flag { font-size: 30px; }
.gi-name { font-size: 16px; font-weight: 700; color: var(--text-primary); }
.gi-vs { color: var(--text-muted); font-size: 16px; font-weight: 700; }
.gi-deadline {
  text-align: center;
  font-size: 12px;
  color: var(--text-secondary);
}
.success-state {
  padding: 40px 24px 16px;
  text-align: center;
  animation: successPop 0.45s cubic-bezier(0.32,0.72,0,1);
}
.success-icon { font-size: 64px; margin-bottom: 18px; line-height: 1; }
.success-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--accent-green);
  margin-bottom: 8px;
  letter-spacing: -0.5px;
}
.success-sub {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
}
.score-section { padding: 24px 24px 0; }
.score-picker {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 24px;
}
.score-team {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}
.score-team-name {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 600;
  text-align: center;
  max-width: 80px;
  line-height: 1.2;
}
.score-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}
.score-btn {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--bg-card-hover);
  border: 1px solid rgba(255,255,255,0.1);
  color: var(--text-primary);
  font-size: 30px;
  font-family: inherit;
  font-weight: 300;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.score-value {
  font-size: 52px;
  font-weight: 700;
  color: var(--text-primary);
  width: 60px;
  text-align: center;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}
.score-divider {
  padding-top: 28px;
  flex-shrink: 0;
  font-size: 24px;
  color: var(--text-muted);
  font-weight: 700;
}
.qs-label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 600;
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
}
.qs-grid {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}
.qs-btn {
  padding: 9px 18px;
  border-radius: 22px;
  font-size: 14px;
  font-weight: 700;
  font-family: inherit;
  background: rgba(255,255,255,0.08);
  color: var(--text-tertiary);
  transition: all 0.12s;
}
.qs-btn.active {
  background: var(--accent-green);
  color: #060E1C;
}
.btn-save {
  width: 100%;
  background: var(--accent-green);
  color: #060E1C;
  border-radius: 14px;
  padding: 18px;
  font-size: 17px;
  font-weight: 700;
  font-family: inherit;
  letter-spacing: -0.2px;
}
</style>
