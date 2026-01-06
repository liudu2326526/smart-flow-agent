import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layout/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: MainLayout,
      redirect: '/chat',
      children: [
        {
          path: 'chat',
          name: 'chat',
          component: () => import('@/views/chat/ChatView.vue')
        },
        {
          path: 'chat/:id',
          name: 'chat-detail',
          component: () => import('@/views/chat/ChatView.vue')
        },
        {
          path: 'knowledge',
          name: 'knowledge',
          component: () => import('@/views/knowledge/DocumentList.vue')
        },
        {
          path: 'settings',
          name: 'settings',
          component: { template: '<div style="padding: 20px">Settings Page (Coming Soon)</div>' } // Placeholder
        }
      ]
    }
  ]
})

export default router
