<template>
  <header class="h-16 bg-white border-b border-light-2 flex items-center justify-between px-6 z-10">
    <div class="flex items-center">
      <button class="mr-4 text-dark-2 hover:text-primary transition-colors" @click="$emit('toggle-sidebar')">
        <i class="fas fa-bars text-xl"></i>
      </button>

      <div class="relative">
        <input
          v-model="keyword"
          type="text"
          placeholder="搜索..."
          class="pl-10 pr-4 py-2 rounded-lg border border-light-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary w-64 transition-all duration-200"
        />
        <i class="fas fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-light-1"></i>
      </div>
    </div>

    <div class="flex items-center space-x-6">
      <button class="relative text-dark-2 hover:text-primary transition-colors">
        <i class="fas fa-bell text-xl"></i>
        <span class="absolute top-0 right-0 w-2 h-2 bg-danger rounded-full"></span>
      </button>

      <UserDropdown />
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref } from "vue";
import UserDropdown from "@/components/common/UserDropdown.vue";

defineEmits<{ (e: "toggle-sidebar"): void }>();
const keyword = ref("");
</script>