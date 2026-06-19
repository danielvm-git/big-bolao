<script setup>
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const tabs = [
  { name: 'Início', icon: '🏠', path: '/' },
  { name: 'Jogos', icon: '⚽', path: '/jogos' },
  { name: 'Ranking', icon: '🏆', path: '/ranking' },
  { name: 'Meus', icon: '🎯', path: '/meus' },
]

function isActive(path) {
  if (path === '/') return route.name === 'Home'
  return route.path.startsWith(path)
}

function bgColor(path) {
  return isActive(path) ? 'rgba(0,220,130,0.08)' : 'transparent'
}
function textColor(path) {
  return isActive(path) ? '#00DC82' : '#445566'
}
</script>

<template>
  <nav class="bottom-nav">
    <button
      v-for="tab in tabs"
      :key="tab.path"
      class="nav-btn"
      :style="{ background: bgColor(tab.path) }"
      @click="router.push(tab.path)"
    >
      <span class="nav-icon">{{ tab.icon }}</span>
      <span class="nav-label" :style="{ color: textColor(tab.path) }">{{ tab.name }}</span>
    </button>
  </nav>
</template>

<style scoped>
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 430px;
  height: 68px;
  background: #0A1728;
  border-top: 1px solid var(--border-subtle);
  display: flex;
  align-items: stretch;
  z-index: 100;
  box-shadow: 0 -4px 20px rgba(0,0,0,0.4);
}
.nav-btn {
  flex: 1;
  background: transparent;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  padding: 8px 0;
  font-family: inherit;
  transition: background 0.15s;
}
.nav-icon {
  font-size: 22px;
  line-height: 1;
}
.nav-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.2px;
}
</style>
