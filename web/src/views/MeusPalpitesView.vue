<script setup>
import { computed } from 'vue'
import { jogosRich, palpitesIdx, loaded, user, rankingRich, scoreLabel } from '../store.js'

const meusTotal = computed(() => {
  if (!user.value) return null
  const tid = Number(user.value.telegram_id)
  const meuRanking = rankingRich.value.find(r => Number(r.telegram_id) === tid)
  return meuRanking || null
})

const meusPalpites = computed(() => {
  if (!user.value) return []
  const tid = Number(user.value.telegram_id)
  return jogosRich.value.map(g => {
    const pal = palpitesIdx.value[g.match_id]?.[tid] || null
    return { ...g, pal, tipo: pal && g.isFinalizado ? scoreLabel(pal, g) : null }
  }).filter(g => g.pal)
})

const exatos = computed(() => meusPalpites.value.filter(g => g.tipo === 'exato').length)
const vencedores = computed(() => meusPalpites.value.filter(g => g.tipo === 'vencedor').length)
const erros = computed(() => meusPalpites.value.filter(g => g.tipo === 'errou').length)
</script>

<template>
  <div class="page page-narrow fade-in">
    <div v-if="!loaded" class="text-center mt-6" style="padding-top:60px">
      <div class="spinner"></div>
    </div>

    <div v-else-if="!user" class="auth-banner mt-4">
      <p>📱 Abra o link enviado pelo bot no Telegram para ver seus palpites.</p>
    </div>

    <template v-else>
      <!-- Header -->
      <div class="card card-p mt-4" style="display:flex;align-items:center;gap:14px">
        <div :style="{ width:'52px', height:'52px', borderRadius:'50%',
          background: rankingRich.find(r=>Number(r.telegram_id)===Number(user.telegram_id))?.color || '#60A5FA',
          display:'flex', alignItems:'center', justifyContent:'center',
          fontSize:'22px', fontWeight:'800', color:'#060E1C', flexShrink:0 }">
          {{ user.nome[0].toUpperCase() }}
        </div>
        <div style="flex:1">
          <div style="font-size:20px;font-weight:700">{{ user.nome }}</div>
          <div v-if="meusTotal" class="text-2 text-sm mt-1">
            #{{ meusTotal.pos }} no ranking · {{ meusTotal.pontos }} pts
          </div>
        </div>
      </div>

      <!-- Stats -->
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:12px">
        <div class="card card-p text-center">
          <div style="font-size:28px;font-weight:800;color:var(--green)">{{ exatos }}</div>
          <div class="text-2 text-sm mt-1">🎯 Exatos</div>
        </div>
        <div class="card card-p text-center">
          <div style="font-size:28px;font-weight:800;color:var(--blue)">{{ vencedores }}</div>
          <div class="text-2 text-sm mt-1">✓ Acertos</div>
        </div>
        <div class="card card-p text-center">
          <div style="font-size:28px;font-weight:800;color:var(--red)">{{ erros }}</div>
          <div class="text-2 text-sm mt-1">✗ Erros</div>
        </div>
      </div>

      <!-- Palpites list -->
      <p class="section-title mt-6">{{ meusPalpites.length }} palpites</p>
      <div style="display:flex;flex-direction:column;gap:8px">
        <div v-for="g in meusPalpites" :key="g.match_id"
          class="card" style="display:flex;align-items:center;gap:12px;padding:12px 16px">
          <!-- Status dot -->
          <div :style="{
            width:'8px', height:'8px', borderRadius:'50%', flexShrink:0,
            background: g.tipo === 'exato' ? 'var(--green)' : g.tipo === 'vencedor' ? 'var(--blue)' :
              g.tipo === 'errou' ? 'var(--red)' : 'var(--text-3)'
          }"></div>
          <!-- Teams -->
          <div style="flex:1;min-width:0">
            <div style="font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
              {{ g.flagA }} {{ g.casa }} × {{ g.fora }} {{ g.flagB }}
            </div>
            <div class="text-2" style="font-size:11px;margin-top:2px">{{ g.date }} · {{ g.grupo }}</div>
          </div>
          <!-- Result -->
          <div v-if="g.isFinalizado && g.resultado" style="text-align:center;flex-shrink:0">
            <div style="font-size:11px;color:var(--text-2)">Resultado</div>
            <div style="font-size:15px;font-weight:800">{{ g.resultado }}</div>
          </div>
          <!-- My palpite -->
          <div style="text-align:center;flex-shrink:0">
            <div style="font-size:11px;color:var(--text-2)">Palpite</div>
            <div class="cell"
              :class="{
                'cell-exato': g.tipo === 'exato',
                'cell-venc': g.tipo === 'vencedor',
                'cell-erro': g.tipo === 'errou',
                'cell-aberto': g.isAberto,
              }"
              style="font-size:15px;font-weight:800"
            >{{ g.pal.a }}–{{ g.pal.b }}</div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
