<template>
  <div class="app-root">
    <div class="app-shell">
      <Sidebar :collapsed="collapsed" @toggle="collapsed = !collapsed" />

      <div class="app-main">
        <Topbar @toggle-sidebar="collapsed = !collapsed" />
        <main class="app-content">
          <slot />
        </main>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import Sidebar from "@/components/common/Sidebar.vue";
import Topbar from "@/components/common/Topbar.vue";

const collapsed = ref(false);
</script>