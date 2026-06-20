<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { loadAll, initUser, loaded, finalizados, total, user } from './store.js'

const route = useRoute()
const router = useRouter()
const version = ref('—')

onMounted(async () => {
  // Pick up ?uid= from bot link
  const params = new URLSearchParams(window.location.search || window.location.hash.split('?')[1] || '')
  const uid = params.get('uid')
  if (uid) {
    await initUser(uid)
    router.replace({ path: route.path, hash: '' })
  }
  loadAll()

  // Fetch version
  fetch('/api/version')
    .then(r => r.json())
    .then(data => { version.value = data.version })
    .catch(() => {})
})

const TABS = [
  { name: 'Dashboard', label: 'Dashboard', icon: '🏆', path: '/' },
  { name: 'Jogos', label: 'Jogos', icon: '⚽', path: '/jogos' },
  { name: 'Meus', label: 'Meus', icon: '🎯', path: '/meus' },
]
</script>

<template>
  <nav class="nav">
    <div class="nav-brand">
      <span>⚽</span><span>Big Bolão</span>
      <span class="nav-badge">Copa 2026</span>
    </div>
    <div class="nav-tabs">
      <button
        v-for="t in TABS" :key="t.name"
        class="nav-tab" :class="{ active: route.name === t.name }"
        @click="router.push(t.path)"
      >{{ t.label }}</button>
    </div>
    <div class="nav-progress" v-if="loaded">
      <span class="nav-dot"></span>
      <span>{{ finalizados }}/{{ total }} finalizados</span>
    </div>
  </nav>

  <router-view />

  <nav class="bottom-nav">
    <button
      v-for="t in TABS" :key="t.name"
      class="bottom-tab" :class="{ active: route.name === t.name }"
      @click="router.push(t.path)"
    >
      <span class="icon">{{ t.icon }}</span>
      <span>{{ t.label }}</span>
    </button>
  </nav>

  <footer class="app-footer">
    <div class="footer-content">
      <span class="footer-left">© 2026 Big Bolão · Copa do Mundo 2026</span>
      <div class="footer-right">
        <a href="https://t.me/JararacasBolao_bot" target="_blank">Telegram</a>
        <span class="footer-version">v{{ version }}</span>
        <a href="https://github.com/danielvm-git/big-bolao" target="_blank">GitHub</a>
      </div>
    </div>
  </footer>
</template>
