import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import './style.css'
import App from './App.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', name: 'Dashboard', component: () => import('./views/DashboardView.vue') },
    { path: '/jogos', name: 'Jogos', component: () => import('./views/JogosView.vue') },
    { path: '/meus', name: 'Meus', component: () => import('./views/MeusPalpitesView.vue') },
  ],
})

createApp(App).use(router).mount('#app')
