<template>
  <div class="font-inter bg-light-3 text-dark min-h-screen flex overflow-hidden">
    <Sidebar :collapsed="collapsed" @toggle="collapsed = !collapsed" />

    <div class="flex-1 flex flex-col overflow-hidden">
      <Topbar @toggle-sidebar="collapsed = !collapsed" />
      <main class="flex-1 overflow-y-auto bg-light-3 p-6">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import Sidebar from "@/components/common/Sidebar.vue";
import Topbar from "@/components/common/Topbar.vue";

const collapsed = ref(false);
</script>