<script setup>
import { ref } from 'vue'
import { useJogos } from '../composables/useJogos.js'
import GameCard from '../components/GameCard.vue'
import PalpiteModal from '../components/PalpiteModal.vue'

const { jogosFiltrados, filtro, setFiltro } = useJogos()
const palpiteTarget = ref(null)
const showModal = ref(false)

const filtros = [
  { key: 'abertos', label: 'Abertos' },
  { key: 'meus', label: 'Meus palpites' },
  { key: 'finalizados', label: 'Finalizados' },
  { key: 'todos', label: 'Todos' },
]

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
    <div class="page-header">
      <h2 class="page-title">⚽ Jogos</h2>
      <p class="page-subtitle">Copa do Mundo 2026</p>
    </div>

    <!-- Filter tabs -->
    <div class="filter-bar">
      <button
        v-for="f in filtros"
        :key="f.key"
        class="filter-btn"
        :class="{ active: filtro === f.key }"
        @click="setFiltro(f.key)"
      >{{ f.label }}</button>
    </div>

    <!-- Games list -->
    <div class="games-list">
      <GameCard
        v-for="game in jogosFiltrados"
        :key="game.id"
        :game="game"
        @palpitar="openPalpite"
      />
    </div>

    <!-- Empty state -->
    <div v-if="jogosFiltrados.length === 0" class="empty-state">
      <p class="empty-icon">🏟️</p>
      <p class="empty-title">Nenhum jogo aqui</p>
      <p class="empty-desc">Tente outro filtro.</p>
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
.filter-bar {
  display: flex;
  gap: 8px;
  padding: 14px 20px 4px;
  overflow-x: auto;
  scrollbar-width: none;
}
.filter-btn {
  flex-shrink: 0;
  padding: 9px 18px;
  border-radius: 22px;
  font-size: 13px;
  font-weight: 600;
  font-family: inherit;
  background: rgba(255,255,255,0.07);
  color: var(--text-secondary);
  transition: all 0.15s;
}
.filter-btn.active {
  background: var(--accent-green);
  color: #060E1C;
}
.games-list {
  padding: 8px 20px 8px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.empty-state {
  text-align: center;
  padding: 52px 24px;
}
.empty-icon { font-size: 52px; margin-bottom: 16px; }
.empty-title {
  font-size: 18px;
  font-weight: 700;
  color: #B0B8C4;
  margin-bottom: 8px;
}
.empty-desc { font-size: 14px; color: var(--text-secondary); }
.spacer { height: 20px; }
</style>
