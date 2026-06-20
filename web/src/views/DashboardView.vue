<script setup>
import { computed } from 'vue'
import { jogosRich, palpitesIdx, rankingRich, loaded, abertos, finalizados, total, scoreLabel, user } from '../store.js'
import { avatarColor } from '../api.js'

// Top 3 leaders
const top3 = computed(() => rankingRich.value.slice(0, 3))

// Recent finalized games (last 5)
const recentGames = computed(() => [...jogosRich.value].filter(g => g.isFinalizado).reverse().slice(0, 5))

// Upcoming games (next 6 open)
const upcomingGames = computed(() => jogosRich.value.filter(g => g.isAberto).slice(0, 6))
</script>

<template>
  <div class="page fade-in">
    <!-- Loading -->
    <div v-if="!loaded" class="text-center mt-6" style="padding-top:60px">
      <div class="spinner"></div>
      <p class="text-2 mt-3">Carregando dados...</p>
    </div>

    <template v-else>
      <!-- Hero stats -->
      <div class="grid-2 mt-4" style="grid-template-columns: repeat(3, 1fr); gap: 12px">
        <div class="card card-p text-center">
          <div style="font-size:32px;font-weight:800;line-height:1">{{ finalizados }}</div>
          <div class="text-2 text-sm mt-1">Finalizados</div>
        </div>
        <div class="card card-p text-center">
          <div style="font-size:32px;font-weight:800;line-height:1">{{ abertos }}</div>
          <div class="text-2 text-sm mt-1">Abertos</div>
        </div>
        <div class="card card-p text-center">
          <div style="font-size:32px;font-weight:800;line-height:1">{{ rankingRich.length }}</div>
          <div class="text-2 text-sm mt-1">Participantes</div>
        </div>
      </div>

      <!-- Layout: ranking + games -->
      <div style="display:grid;grid-template-columns:300px 1fr;gap:20px;margin-top:20px;align-items:start">

        <!-- LEFT: Ranking -->
        <div>
          <p class="section-title">🏆 Ranking</p>
          <div class="card">
            <div
              v-for="(r, i) in rankingRich"
              :key="r.telegram_id"
              class="rank-row"
              :style="i === 0 ? 'background:rgba(247,201,72,.04)' : ''"
            >
              <span class="rank-pos">{{ r.pos }}</span>
              <span v-if="r.medal" style="font-size:18px;flex-shrink:0">{{ r.medal }}</span>
              <div class="rank-avatar" :style="{ background: r.color }">{{ r.initial }}</div>
              <div class="rank-info">
                <div class="rank-name" :style="i === 0 ? 'color:var(--gold)' : ''">{{ r.nome }}</div>
                <div class="rank-sub">{{ r.exatos }} exato(s) · {{ r.acertos }} acerto(s)</div>
              </div>
              <div class="rank-pts" :style="i === 0 ? 'color:var(--gold)' : ''">
                {{ r.pontos }}<span style="font-size:12px;color:var(--text-2);font-weight:500"> pts</span>
              </div>
            </div>
          </div>

          <!-- Como pontuar -->
          <p class="section-title mt-6">Como pontuar</p>
          <div class="card card-p" style="display:flex;flex-direction:column;gap:10px">
            <div class="flex items-center gap-2">
              <span style="font-size:20px;font-weight:800;color:var(--green)">+3</span>
              <span class="text-2 text-sm">🎯 Placar exato</span>
            </div>
            <div class="flex items-center gap-2">
              <span style="font-size:20px;font-weight:800;color:var(--blue)">+1</span>
              <span class="text-2 text-sm">✓ Vencedor ou empate certo</span>
            </div>
            <div class="flex items-center gap-2">
              <span style="font-size:20px;font-weight:800;color:var(--text-3)">0</span>
              <span class="text-2 text-sm">✗ Erro</span>
            </div>
          </div>
        </div>

        <!-- RIGHT: Games -->
        <div>
          <!-- Recent results -->
          <div v-if="recentGames.length">
            <p class="section-title">Últimos resultados</p>
            <div style="display:flex;flex-direction:column;gap:10px;margin-bottom:20px">
              <div v-for="g in recentGames" :key="g.match_id" class="game-card">
                <div class="game-head">
                  <span class="game-status status-encerrado">Finalizado</span>
                  <span class="text-2" style="font-size:12px">{{ g.date }} · {{ g.time }} · {{ g.grupo }}</span>
                </div>
                <div class="game-teams">
                  <div class="game-team">
                    <span class="game-flag">{{ g.flagA }}</span>
                    <span class="game-name">{{ g.casa }}</span>
                  </div>
                  <span class="game-result">{{ g.resultado }}</span>
                  <div class="game-team right">
                    <span class="game-name">{{ g.fora }}</span>
                    <span class="game-flag">{{ g.flagB }}</span>
                  </div>
                </div>
                <!-- Palpites -->
                <div class="game-guesses">
                  <span class="guess-label">Palpites</span>
                  <template v-for="(r, i) in rankingRich" :key="r.telegram_id">
                    <div
                      v-if="palpitesIdx[g.match_id]?.[r.telegram_id]"
                      class="guess-chip"
                      :class="scoreLabel(palpitesIdx[g.match_id]?.[r.telegram_id], g)"
                    >
                      <div class="guess-avatar" :style="{ background: r.color }">{{ r.initial }}</div>
                      <span class="guess-score">
                        {{ palpitesIdx[g.match_id][r.telegram_id].a }}–{{ palpitesIdx[g.match_id][r.telegram_id].b }}
                      </span>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>

          <!-- Upcoming -->
          <div v-if="upcomingGames.length">
            <p class="section-title">Próximos jogos</p>
            <div style="display:flex;flex-direction:column;gap:10px">
              <div v-for="g in upcomingGames" :key="g.match_id" class="game-card">
                <div class="game-head">
                  <span class="game-status status-aberto">Aberto</span>
                  <span class="text-2" style="font-size:12px">{{ g.date }} · {{ g.time }} · {{ g.grupo }}</span>
                </div>
                <div class="game-teams">
                  <div class="game-team">
                    <span class="game-flag">{{ g.flagA }}</span>
                    <span class="game-name">{{ g.casa }}</span>
                  </div>
                  <span class="game-score">×</span>
                  <div class="game-team right">
                    <span class="game-name">{{ g.fora }}</span>
                    <span class="game-flag">{{ g.flagB }}</span>
                  </div>
                </div>
                <div class="game-guesses" v-if="Object.keys(palpitesIdx[g.match_id] || {}).length">
                  <span class="guess-label">Palpites</span>
                  <template v-for="r in rankingRich" :key="r.telegram_id">
                    <div v-if="palpitesIdx[g.match_id]?.[r.telegram_id]" class="guess-chip">
                      <div class="guess-avatar" :style="{ background: r.color }">{{ r.initial }}</div>
                      <span class="guess-score">
                        {{ palpitesIdx[g.match_id][r.telegram_id].a }}–{{ palpitesIdx[g.match_id][r.telegram_id].b }}
                      </span>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Cross table -->
      <div class="mt-6">
        <p class="section-title">Todos os palpites</p>
        <div class="card" style="padding:16px">
          <div class="xtable-wrap">
            <table class="xtable">
              <thead>
                <tr>
                  <th class="game-col">Jogo</th>
                  <th>Placar</th>
                  <th v-for="r in rankingRich" :key="r.telegram_id">
                    <div :style="{ width:'32px', height:'32px', borderRadius:'50%', background:r.color,
                      display:'flex', alignItems:'center', justifyContent:'center',
                      margin:'0 auto 2px', fontSize:'12px', fontWeight:'700', color:'#060E1C' }">
                      {{ r.initial }}
                    </div>
                    <div>{{ r.nome.split(' ')[0] }}</div>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="g in jogosRich" :key="g.match_id">
                  <td class="game-col">
                    <span>{{ g.flagA }} {{ g.casa }} × {{ g.fora }} {{ g.flagB }}</span>
                    <div class="sub text-2">{{ g.date }} · {{ g.grupo }}</div>
                  </td>
                  <td class="result-col">{{ g.resultado || '–' }}</td>
                  <td v-for="r in rankingRich" :key="r.telegram_id">
                    <span
                      v-if="palpitesIdx[g.match_id]?.[r.telegram_id]"
                      class="cell"
                      :class="{
                        'cell-exato': scoreLabel(palpitesIdx[g.match_id]?.[r.telegram_id], g) === 'exato',
                        'cell-venc': scoreLabel(palpitesIdx[g.match_id]?.[r.telegram_id], g) === 'vencedor',
                        'cell-erro': scoreLabel(palpitesIdx[g.match_id]?.[r.telegram_id], g) === 'errou',
                        'cell-aberto': g.isAberto,
                      }"
                    >
                      {{ palpitesIdx[g.match_id][r.telegram_id].a }}–{{ palpitesIdx[g.match_id][r.telegram_id].b }}
                    </span>
                    <span v-else class="cell cell-sem">–</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
