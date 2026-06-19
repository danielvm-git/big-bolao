import { ref, computed, watch } from 'vue'
import { useAuth } from './useAuth.js'
import { fetchParticipantes, fetchAllPalpites, fetchJogos, calcRanking } from '../api.js'
import { RANKING } from '../data/mock.js' // fallback

const rankingData = ref([])
const loaded = ref(false)

export function useRanking() {
  const { user, isLoggedIn } = useAuth()

  watch(isLoggedIn, async (val) => {
    if (!val || loaded.value) return
    try {
      const [jogos, palpites, participantes] = await Promise.all([
        fetchJogos(), fetchAllPalpites(), fetchParticipantes(),
      ])
      rankingData.value = calcRanking(jogos, palpites, participantes)
      loaded.value = true
    } catch (e) {
      console.warn('Ranking fetch failed, using mock:', e.message)
      rankingData.value = [...RANKING]
      loaded.value = true
    }
  })

  const COLORS = ['#F7C948', '#94A3B8', '#CD7F32', '#60A5FA', '#A78BFA', '#4ADE80', '#F87171']

  const rankingList = computed(() =>
    rankingData.value.map((r, i) => ({
      ...r,
      id: r.telegram_id || i,
      name: r.nome,
      pontos: r.pontos,
      exatos: r.exatos,
      posicao: i + 1,
      isMe: user.value ? Number(r.telegram_id) === Number(user.value.telegram_id) : false,
      medal: i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : '',
      avatarColor: COLORS[i % COLORS.length],
      initial: (r.nome || '?')[0],
    }))
  )

  const top3 = computed(() => rankingList.value.slice(0, 3))

  const podium = computed(() => {
    if (rankingList.value.length < 3) return [null, null, null]
    return [rankingList.value[1], rankingList.value[0], rankingList.value[2]]
  })

  return { rankingList, top3, podium, loaded }
}
