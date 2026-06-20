<script setup>
import { ref, computed } from 'vue'
import { jogosRich, palpitesIdx, loaded, user, reloadPalpites } from '../store.js'
import { savePalpite } from '../api.js'

const modal = ref(null) // { jogo, goalsA, goalsB }
const saving = ref(false)

const jogosAbertos = computed(() => jogosRich.value.filter(g => g.isAberto))

function myPalpite(matchId) {
  if (!user.value) return null
  return palpitesIdx.value[matchId]?.[Number(user.value.telegram_id)] || null
}

function openModal(jogo) {
  const pal = myPalpite(jogo.match_id)
  modal.value = { jogo, goalsA: pal?.a ?? 0, goalsB: pal?.b ?? 0 }
}

function closeModal() { modal.value = null }

async function saveCurrent() {
  if (!modal.value || !user.value) return
  saving.value = true
  const { jogo, goalsA, goalsB } = modal.value
  await savePalpite(jogo.match_id, user.value.telegram_id, user.value.nome, goalsA, goalsB)
  await reloadPalpites()
  saving.value = false
  modal.value = null
}
</script>

<template>
  <div class="page page-narrow fade-in">
    <div v-if="!loaded" class="text-center mt-6" style="padding-top:60px">
      <div class="spinner"></div>
      <p class="text-2 mt-3">Carregando...</p>
    </div>

    <template v-else>
      <!-- Auth banner if not logged in -->
      <div v-if="!user" class="auth-banner mt-4">
        <p>📱 Para palpitar, abra o link enviado pelo bot no Telegram.<br>
          <span style="font-size:12px;margin-top:4px;display:block">
            O link tem o formato: bolao.bigbase.click?uid=SEU_ID
          </span>
        </p>
      </div>

      <!-- User badge -->
      <div v-else class="flex items-center gap-2 mt-4 mb-2"
        style="background:rgba(0,220,130,.06);border:1px solid rgba(0,220,130,.15);
          border-radius:10px;padding:10px 14px">
        <span style="font-size:20px">👋</span>
        <span class="font-bold">{{ user.nome }}</span>
        <span class="text-2 text-sm">— seus palpites</span>
      </div>

      <p class="section-title mt-4">{{ jogosAbertos.length }} jogos abertos</p>

      <div style="display:flex;flex-direction:column;gap:12px;margin-top:8px">
        <div v-for="g in jogosAbertos" :key="g.match_id" class="game-card">
          <div class="game-head">
            <span class="game-status status-aberto">Aberto</span>
            <span class="text-2" style="font-size:12px">{{ g.date }} · {{ g.time }} · {{ g.grupo }}</span>
          </div>
          <div class="game-teams">
            <div class="game-team">
              <span class="game-flag">{{ g.flagA }}</span>
              <span class="game-name">{{ g.casa }}</span>
            </div>
            <span class="game-score" style="color:var(--text-3)">×</span>
            <div class="game-team right">
              <span class="game-name">{{ g.fora }}</span>
              <span class="game-flag">{{ g.flagB }}</span>
            </div>
          </div>
          <!-- My palpite -->
          <button
            v-if="user"
            class="palpite-btn"
            :class="{ saved: !!myPalpite(g.match_id) }"
            @click="openModal(g)"
          >
            <span v-if="myPalpite(g.match_id)">
              ✓ {{ myPalpite(g.match_id).a }}–{{ myPalpite(g.match_id).b }} · Editar
            </span>
            <span v-else>Palpitar →</span>
          </button>
        </div>
      </div>
    </template>

    <!-- Modal -->
    <teleport to="body">
      <div v-if="modal" class="modal-bg" @click.self="closeModal">
        <div class="modal" style="position:relative">
          <button class="modal-close" @click="closeModal">✕</button>
          <p class="modal-title">Seu palpite</p>
          <div class="modal-teams">
            <div class="modal-team">
              <div class="modal-flag">{{ modal.jogo.flagA }}</div>
              <div class="modal-name">{{ modal.jogo.casa }}</div>
            </div>
            <div class="modal-score">
              <div class="score-col">
                <button class="score-btn" @click="modal.goalsA = Math.min(20, modal.goalsA + 1)">+</button>
                <div class="score-val">{{ modal.goalsA }}</div>
                <button class="score-btn" @click="modal.goalsA = Math.max(0, modal.goalsA - 1)">−</button>
              </div>
              <div class="score-sep">×</div>
              <div class="score-col">
                <button class="score-btn" @click="modal.goalsB = Math.min(20, modal.goalsB + 1)">+</button>
                <div class="score-val">{{ modal.goalsB }}</div>
                <button class="score-btn" @click="modal.goalsB = Math.max(0, modal.goalsB - 1)">−</button>
              </div>
            </div>
            <div class="modal-team">
              <div class="modal-flag">{{ modal.jogo.flagB }}</div>
              <div class="modal-name">{{ modal.jogo.fora }}</div>
            </div>
          </div>
          <button class="modal-save" :disabled="saving" @click="saveCurrent">
            {{ saving ? 'Salvando...' : 'Salvar palpite' }}
          </button>
        </div>
      </div>
    </teleport>
  </div>
</template>
