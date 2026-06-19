<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'

const route = useRoute()
const router = useRouter()
const { loginWithTelegramId, loginMock } = useAuth()

const loading = ref(true)
const error = ref('')
const userName = ref('')

onMounted(async () => {
  // Check for uid in URL (bot sends ?uid=<telegram_id>)
  // Supports both hash and normal query params
  const params = new URLSearchParams(window.location.search || window.location.hash.split('?')[1] || '')
  const uid = route.query.uid || params.get('uid')
  if (uid) {
    const ok = await loginWithTelegramId(uid)
    if (ok) {
      router.replace({ query: {} }) // clean URL
      return // redirect will happen in App.vue
    } else {
      error.value = `Usuário com ID ${uid} não encontrado no bolão.`
    }
  }
  loading.value = false
})

function handleLogin() {
  loginMock()
}

function handleRetry() {
  error.value = ''
  loading.value = false
}
</script>

<template>
  <div class="login-screen">
    <div class="login-content">
      <div class="login-brand">
        <div class="login-ball">⚽</div>
        <h1 class="login-title">Big Bolão</h1>
        <p class="login-subtitle">COPA DO MUNDO 2026</p>
      </div>

      <!-- Loading -->
      <div v-if="loading && !error" class="login-card loading-card">
        <p class="loading-icon">⏳</p>
        <p class="loading-text">Verificando seu acesso...</p>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="login-card error-card">
        <p class="error-icon">⚠️</p>
        <p class="error-text">{{ error }}</p>
        <p class="error-hint">Peça ao admin do bolão pra te enviar o link de acesso pelo Telegram.</p>
        <button class="login-btn retry" @click="handleRetry">Tentar com usuário de teste</button>
      </div>

      <!-- Default: no uid in URL -->
      <div v-else class="login-card">
        <p class="login-card-label">📱 Acesso pelo Telegram</p>
        <p class="login-desc">
          Abra o link enviado pelo bot no Telegram para acessar o bolão.
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-screen {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 40px 24px;
  background: linear-gradient(160deg, #060E1C 0%, #0B2145 55%, #060E1C 100%);
}
.login-content { width: 100%; max-width: 380px; text-align: center; }
.login-brand { margin-bottom: 48px; animation: fadeInUp 0.5s ease both; }
.login-ball { font-size: 80px; margin-bottom: 16px; filter: drop-shadow(0 0 24px rgba(0,220,130,0.35)); }
.login-title { font-size: 38px; font-weight: 700; color: var(--text-primary); letter-spacing: -1px; line-height: 1; }
.login-subtitle { font-size: 15px; color: var(--accent-gold); font-weight: 600; margin-top: 6px; letter-spacing: 0.5px; }
.login-desc { font-size: 13px; color: var(--text-secondary); margin-top: 8px; }
.login-card {
  width: 100%;
  background: var(--bg-card);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 22px;
  padding: 28px 24px;
  animation: fadeInUp 0.5s ease 0.12s both;
}
.login-card-label { font-size: 11px; color: var(--text-secondary); text-align: center; margin-bottom: 18px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
.login-user-card {
  display: flex; align-items: center; gap: 14px;
  background: var(--bg-card-hover); border-radius: 16px; padding: 16px; margin-bottom: 20px;
  border: 1px solid rgba(0,220,130,0.1);
}
.login-avatar {
  width: 52px; height: 52px; border-radius: 50%;
  background: linear-gradient(135deg, #60A5FA, #A78BFA);
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; font-weight: 700; color: white; flex-shrink: 0;
  box-shadow: 0 0 16px rgba(96,165,250,0.3);
}
.login-user-name { font-size: 20px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.3px; }
.login-user-info { font-size: 13px; color: var(--text-secondary); margin-top: 2px; }
.login-btn {
  width: 100%; background: var(--accent-green); color: #060E1C; border: none;
  border-radius: 14px; padding: 18px; font-size: 17px; font-weight: 700;
  cursor: pointer; font-family: inherit; letter-spacing: -0.2px;
}
.login-btn.retry { background: var(--accent-gold-dim); color: var(--accent-gold); }
.loading-card { padding: 48px 24px; }
.loading-icon { font-size: 48px; margin-bottom: 16px; }
.loading-text { font-size: 16px; color: var(--text-secondary); }
.error-card { padding: 36px 24px; border-color: rgba(248,113,113,0.2); }
.error-icon { font-size: 40px; margin-bottom: 12px; }
.error-text { font-size: 15px; color: var(--accent-red); font-weight: 600; margin-bottom: 10px; }
.error-hint { font-size: 13px; color: var(--text-secondary); margin-bottom: 18px; line-height: 1.5; }

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(18px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
