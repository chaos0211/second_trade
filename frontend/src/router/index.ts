import { createRouter, createWebHistory } from 'vue-router'
import MarketplaceView from '../views/MarketplaceView.vue'
import Register from "../views/Register.vue";
import Login from "../views/Login.vue";
import SellDeviceView from "../views/SellDeviceView.vue";
import OrderCenterView from "../views/OrderCenterView.vue";
import ProfileView from "../views/ProfileView.vue";
import AdminUsersView from "../views/AdminUsersView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {path: '/', name: 'marketplace', component: MarketplaceView,},
    {path: '/register', name: 'register', component: Register,},
    {path: '/login', name: 'login', component: Login,},
    {path: '/seller', name: 'seller', component: SellDeviceView,},
    {path: '/orders', name: 'orders', component: OrderCenterView,},
    {path: '/profile', name: 'profile', component: ProfileView,},
    {path: '/admin', name: 'admin', component: AdminUsersView,},
  ],
})

export default router