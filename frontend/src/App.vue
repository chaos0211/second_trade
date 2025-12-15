<template>
  <!-- 登录 / 注册页面不使用主布局 -->
  <RouterView v-if="isAuthRoute" />

  <!-- 其它业务页面使用主布局 -->
  <DefaultLayout v-else>
    <RouterView />
  </DefaultLayout>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { RouterView, useRoute } from "vue-router";
import DefaultLayout from "@/layouts/DefaultLayout.vue";

const route = useRoute();

// 识别登录/注册等鉴权页面
const isAuthRoute = computed(() => {
  const path = route.path;
  return path === "/login" || path === "/register";
});
</script>