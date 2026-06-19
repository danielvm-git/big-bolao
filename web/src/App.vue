<script setup>
import { useRoute } from 'vue-router'
import { useAuth } from './composables/useAuth.js'
import BottomNav from './components/BottomNav.vue'
import LoginView from './views/LoginView.vue'

const route = useRoute()
const { isLoggedIn } = useAuth()
</script>

<template>
  <div class="app-shell" :class="{ 'is-logged-in': isLoggedIn }">
    <div class="app-screen" :class="{ 'is-logged-in': isLoggedIn }">
      <LoginView v-if="!isLoggedIn && route.name !== 'Login'" class="login-overlay" />
<!--
  LAYOUT HARDENING (BUG-2026-06-19-183500):
  - router-view MUST be always mounted (never inside v-if/v-else)
  - Do NOT use <router-view v-slot="..."> with <transition> — it breaks route resolution
  - LoginView overlays via position:absolute instead of replacing router-view
 -->
      <router-view />
      <BottomNav v-if="isLoggedIn" />
    </div>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: #030B16;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}
.app-screen {
  width: 100%;
  max-width: 430px;
  min-height: 100vh;
  background: #060E1C;
  display: flex;
  flex-direction: column;
  position: relative;
}
.app-screen.is-logged-in {
  padding-bottom: 68px;
}
.login-overlay {
  position: absolute;
  inset: 0;
  z-index: 50;
  background: var(--bg-surface);
}
</style>
