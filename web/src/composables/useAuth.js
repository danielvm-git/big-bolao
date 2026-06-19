import { ref, computed } from 'vue'

const user = ref(null)
const telegramId = ref(null)

export function useAuth() {
  const isLoggedIn = computed(() => !!user.value)

  /** Login via telegram_id from URL (bot sends ?uid=12345 link) */
  async function loginWithTelegramId(uid) {
    if (!uid) return false
    const id = Number(uid)
    telegramId.value = id

    // Fetch user info from BigBase
    try {
      const { fetchParticipantes } = await import('../api.js')
      const parts = await fetchParticipantes()
      const found = parts.find(p => Number(p.telegram_id) === id)
      if (found) {
        user.value = {
          id: found.id,
          nome: found.nome || 'Participante',
          telegram_id: id,
          pontos: 0, // will be computed by ranking
          exatos: 0,
        }
        return true
      }
    } catch (e) {
      console.error('Failed to fetch user:', e)
    }
    return false
  }

  /** Fallback mock login for dev without BigBase token */
  function loginMock() {
    import('../data/mock.js').then(({ USUARIO }) => {
      user.value = { ...USUARIO }
      telegramId.value = USUARIO.telegram_id
    })
  }

  function logout() {
    user.value = null
    telegramId.value = null
  }

  return { user, telegramId, isLoggedIn, loginWithTelegramId, loginMock, logout }
}
