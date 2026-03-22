import { createRouter, createWebHistory } from 'vue-router'
import DashboardPage from '@/pages/DashboardPage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: DashboardPage },
    { path: '/modules', component: () => import('@/pages/ModulesPage.vue') },
    { path: '/modules/:name', component: () => import('@/pages/ModulesPage.vue') },
    { path: '/search', component: () => import('@/pages/SearchPage.vue') },
    { path: '/relationships', component: () => import('@/pages/RelationshipsPage.vue') },
    { path: '/resources', component: () => import('@/pages/ResourcesPage.vue') },
    { path: '/playground', component: () => import('@/pages/PlaygroundPage.vue') },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

export default router
