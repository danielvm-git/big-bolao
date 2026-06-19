import { computed } from 'vue'
import { useJogos } from './useJogos.js'
import { useAuth } from './useAuth.js'

export function usePalpites() {
  const { user } = useAuth()
  const { jogos } = useJogos()

  const meusAbertos = computed(() => jogos.value.filter(g => g.isAberto && g.hasPalpite))
  const meusBloqueados = computed(() => jogos.value.filter(g => g.isBloqueado && g.hasPalpite))
  const meusFinalizados = computed(() => jogos.value.filter(g => g.isFinalizado && g.hasPalpite))
  const totalPalpites = computed(() => meusAbertos.value.length + meusBloqueados.value.length + meusFinalizados.value.length)

  return { meusAbertos, meusBloqueados, meusFinalizados, totalPalpites }
}
