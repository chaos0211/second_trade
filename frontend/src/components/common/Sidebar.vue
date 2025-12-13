<template>
  <aside
    class="bg-white shadow-lg z-20 flex flex-col transition-all duration-300 ease-in-out"
    :class="collapsed ? 'w-20' : 'w-64'"
  >
    <!-- Logo -->
    <div class="flex items-center justify-center h-16 border-b border-light-2">
      <div class="flex items-center space-x-2">
        <span class="text-xl font-bold text-dark" :class="collapsed ? 'hidden' : ''">二手电子产品交易中心</span>
      </div>
    </div>

    <!-- User -->
    <div class="p-4 border-b border-light-2">
      <div class="flex items-center space-x-3">
        <img
          src="https://design.gemcoder.com/staticResource/echoAiSystemImages/4db1f4e22c08cab67f2bb5c522cad076.png"
          class="w-10 h-10 rounded-full object-cover border-2 border-light-2"
          alt="用户头像"
        />
        <div :class="collapsed ? 'hidden' : ''">
          <h3 class="font-medium text-dark">张小明</h3>
          <div class="flex items-center text-xs text-dark-2">
            <span class="inline-block w-2 h-2 rounded-full bg-success mr-1"></span>
            <span>信用良好</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Nav -->
    <nav class="flex-1 overflow-y-auto scrollbar-hide py-4">
      <ul class="px-2">
        <li class="mb-1">
          <RouterLink
            to="/"
            class="flex items-center space-x-3 py-3 rounded-lg group transition-all duration-200"
            :class="[
              collapsed ? 'justify-center px-2' : 'px-4',
              isMarket ? 'bg-light-3 text-primary' : 'text-dark-2 hover:bg-light-3'
            ]"
          >
            <i class="fas fa-th-large w-5 text-center"></i>
            <span :class="collapsed ? 'hidden' : ''">市场大厅</span>
          </RouterLink>
        </li>

        <li class="mb-1" v-for="item in menus" :key="item.text">
          <RouterLink
            :to="item.to"
            class="flex items-center space-x-3 py-3 rounded-lg group transition-all duration-200"
            :class="[
              collapsed ? 'justify-center px-2' : 'px-4',
              isActive(item.to) ? 'bg-light-3 text-primary' : 'text-dark-2 hover:bg-light-3'
            ]"
          >
            <i :class="item.icon + ' w-5 text-center'"></i>
            <span :class="collapsed ? 'hidden' : ''">{{ item.text }}</span>
          </RouterLink>
        </li>
      </ul>
    </nav>

    <!-- Bottom -->
    <div class="p-4 border-t border-light-2">
      <a
        href="javascript:void(0);"
        class="flex items-center space-x-3 py-3 rounded-lg text-dark-2 group transition-all duration-200 hover:bg-light-3"
        :class="collapsed ? 'justify-center px-2' : 'px-4'"
      >
        <i class="fas fa-question-circle w-5 text-center"></i>
        <span :class="collapsed ? 'hidden' : ''">帮助中心</span>
      </a>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

defineProps<{ collapsed: boolean }>();
defineEmits<{ (e: "toggle"): void }>();

const menus = [
  { icon: "fas fa-tag", text: "我要卖机", to: "/seller" },
  { icon: "fas fa-shopping-cart", text: "订单中心", to: "/orders" },
  { icon: "fas fa-user-circle", text: "个人中心", to: "/profile" },
  { icon: "fas fa-cog", text: "系统管理", to: "/admin" },
];

const route = useRoute();

const isMarket = computed(() => route.path === "/");

function isActive(prefix: string) {
  return route.path === prefix || route.path.startsWith(prefix + "/");
}
</script>