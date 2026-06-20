// Pure scoring and formatting logic — no I/O, no side effects.

export function calcPontos(pa, pb, ra, rb) {
  if (pa === ra && pb === rb) return 3
  const s = (x, y) => x > y ? 1 : x < y ? -1 : 0
  return s(pa, pb) === s(ra, rb) ? 1 : 0
}

// Flags
const FLAGS = {
  brazil:'🇧🇷',brasil:'🇧🇷',argentina:'🇦🇷',mexico:'🇲🇽','estados unidos':'🇺🇸',usa:'🇺🇸',canada:'🇨🇦',
  germany:'🇩🇪',alemanha:'🇩🇪',spain:'🇪🇸',espanha:'🇪🇸',france:'🇫🇷',franca:'🇫🇷',england:'🏴󠁧󠁢󠁥󠁮󠁧󠁿',
  portugal:'🇵🇹',netherlands:'🇳🇱','paises baixos':'🇳🇱',belgium:'🇧🇪',belgica:'🇧🇪',
  italy:'🇮🇹',italia:'🇮🇹',croatia:'🇭🇷',croacia:'🇭🇷',uruguay:'🇺🇾',uruguai:'🇺🇾',
  colombia:'🇨🇴',ecuador:'🇪🇨',equador:'🇪🇨',paraguay:'🇵🇾',paraguai:'🇵🇾',chile:'🇨🇱',
  morocco:'🇲🇦',marrocos:'🇲🇦',senegal:'🇸🇳',algeria:'🇩🇿',argelia:'🇩🇿',
  'ivory coast':'🇨🇮','costa do marfim':'🇨🇮',ghana:'🇬🇭',gana:'🇬🇭',
  japan:'🇯🇵',japao:'🇯🇵','south korea':'🇰🇷','coreia do sul':'🇰🇷',
  'saudi arabia':'🇸🇦','arabia saudita':'🇸🇦',australia:'🇦🇺',iran:'🇮🇷',
  sweden:'🇸🇪',suecia:'🇸🇪',norway:'🇳🇴',noruega:'🇳🇴',switzerland:'🇨🇭',suica:'🇨🇭',
  turkey:'🇹🇷',turquia:'🇹🇷',austria:'🇦🇹',scotland:'🏴󠁧󠁢󠁳󠁣󠁴󠁿',escocia:'🏴󠁧󠁢󠁳󠁣󠁴󠁿',
  haiti:'🇭🇹',curacao:'🇨🇼','cape verde':'🇨🇻','cabo verde':'🇨🇻',panama:'🇵🇦',
  qatar:'🇶🇦',catar:'🇶🇦','new zealand':'🇳🇿','nova zelandia':'🇳🇿',
  'dr congo':'🇨🇩','republica democratica do congo':'🇨🇩',egypt:'🇪🇬',egito:'🇪🇬',
  iraq:'🇮🇶',iraque:'🇮🇶',jordan:'🇯🇴',jordania:'🇯🇴',uzbekistan:'🇺🇿',uzbequistao:'🇺🇿',
  tunisia:'🇹🇳','south africa':'🇿🇦','africa do sul':'🇿🇦',
  'bosnia and herzegovina':'🇧🇦','bosnia e herzegovina':'🇧🇦','bosnia herzegovina':'🇧🇦',
  'czech republic':'🇨🇿',czechia:'🇨🇿','republica tcheca':'🇨🇿',
}

function _normTeam(team) {
  return team.toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9 ]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

export function flag(team) {
  if (!team) return '🏳️'
  return FLAGS[_normTeam(team)] || '🏳️'
}

export function fmtDate(iso) {
  if (!iso) return ''
  const [,m,d] = iso.split('T')[0].split('-')
  return `${d}/${m}`
}
export function fmtTime(iso) {
  if (!iso) return ''
  return iso.split('T')[1]?.slice(0,5) || ''
}

const COLORS = ['#F7C948','#94A3B8','#CD7F32','#60A5FA','#A78BFA','#4ADE80','#F87171','#FB923C']
export function avatarColor(i) { return COLORS[i % COLORS.length] }

export function calcRanking(jogos, palpites, participantes) {
  const ativos = participantes.filter(p => p.ativo !== false && Number(p.telegram_id) > 0)
  const nomes = Object.fromEntries(ativos.map(p => [Number(p.telegram_id), p.nome || '?']))
  const enc = {}
  for (const j of jogos) {
    if (j.status === 'encerrado' && j.gols_casa != null)
      enc[j.match_id] = [Number(j.gols_casa), Number(j.gols_fora)]
  }
  const acc = {}
  for (const p of palpites) {
    const tid = Number(p.telegram_id)
    if (!nomes[tid] || !enc[p.match_id]) continue
    const [ra, rb] = enc[p.match_id]
    const pts = calcPontos(Number(p.gols_casa), Number(p.gols_fora), ra, rb)
    const e = acc[tid] || (acc[tid] = { telegram_id: tid, nome: nomes[tid], pontos: 0, exatos: 0, acertos: 0 })
    e.pontos += pts
    if (pts === 3) e.exatos++
    if (pts >= 1) e.acertos++
  }
  for (const tid of Object.keys(nomes)) {
    if (!acc[tid]) acc[Number(tid)] = { telegram_id: Number(tid), nome: nomes[tid], pontos: 0, exatos: 0, acertos: 0 }
  }
  return Object.values(acc).sort((a, b) => b.pontos - a.pontos || b.exatos - a.exatos || a.nome.localeCompare(b.nome))
}
