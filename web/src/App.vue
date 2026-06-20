<script setup>
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { loadAll, initUser, loaded, finalizados, total, user } from './store.js'

const route = useRoute()
const router = useRouter()

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
</template>
