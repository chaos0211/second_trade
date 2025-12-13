import { createRouter, createWebHistory } from 'vue-router'
import MarketplaceView from '../views/MarketplaceView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'marketplace',
      component: MarketplaceView,
    },
  ],
})

export default router