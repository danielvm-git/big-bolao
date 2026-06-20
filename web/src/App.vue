<script setup>
import { useRoute } from 'vue-router'
import { useAuth } from './composables/useAuth.js'
import BottomNav from './components/BottomNav.vue'

const route = useRoute()
const { isLoggedIn } = useAuth()
</script>

<template>
  <div class="app-shell">
    <div class="app-screen">
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
  padding-bottom: 68px;
}
</style>
