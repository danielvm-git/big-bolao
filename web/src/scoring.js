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
