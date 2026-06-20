<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { loadAll, initUser, loaded, finalizados, total, user } from './store.js'

const route = useRoute()
const router = useRouter()
// __APP_VERSION__ is replaced at build time by Vite's define (CSP-safe).
const version = ref(__APP_VERSION__)

onMounted(async () => {
  // Pick up ?uid= from bot link
  const params = new URLSearchParams(window.location.search || window.location.hash.split('?')[1] || '')
  const uid = params.get('uid')
  if (uid) {
    await initUser(uid)
    router.replace({ path: route.path, hash: '' })
  }
  loadAll()
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
        <span class="footer-version">v{{ version }}</span>
        <span class="footer-built">Built with
          <a href="https://github.com/danielvm-git/BigPowers" target="_blank" class="footer-bigpowers">BigPowers</a>
          by <a href="https://github.com/danielvm-git" target="_blank">danielvm-git</a>
        </span>
        <a href="https://github.com/danielvm-git/big-bolao" target="_blank">GitHub</a>
        <a href="https://github.com/danielvm-git/big-bolao/blob/main/CHANGELOG.md" target="_blank">Changelog</a>
      </div>
    </div>
  </footer>
</template>
