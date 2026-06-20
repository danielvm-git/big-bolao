// Re-export pure modules for backward compatibility
// New code should import directly from transport.js, queries.js, or scoring.js
export { calcPontos, calcRanking, flag, fmtDate, fmtTime, avatarColor } from './scoring.js'
export { BB } from './transport.js'
export { fetchJogos, fetchParticipantes, fetchAllPalpites, fetchPalpitesDoUsuario, savePalpite, findUser } from './queries.js'


