export default [
  { path: '/login', name: 'Login', component: () => import('../views/LoginView.vue') },
  { path: '/', name: 'Home', component: () => import('../views/HomeView.vue') },
  { path: '/jogos', name: 'Jogos', component: () => import('../views/JogosView.vue') },
  { path: '/ranking', name: 'Ranking', component: () => import('../views/RankingView.vue') },
  { path: '/meus', name: 'MeusPalpites', component: () => import('../views/MeusPalpitesView.vue') },
  { path: '/resultado/:id', name: 'Resultado', component: () => import('../views/ResultadoView.vue') },
  { path: '/dashboard', name: 'Dashboard', component: () => import('../views/DashboardView.vue') },
]
