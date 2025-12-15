<template>
  <div>
    <div v-if="sellerId == null" class="p-6 text-sm text-neutral-600">
      加载中...
    </div>

    <SellProductList
      v-else
      :key="listKey"
      :sellerId="sellerId"
      @open-wizard="wizardOpen = true"
      @view="onView"
      @edit="onEdit"
      @unlist="onUnlist"
    />

    <Teleport to="body">
      <SellWizard
        v-if="wizardOpen"
        v-model:open="wizardOpen"
        @close="wizardOpen = false"
        @success="onPublishSuccess"
      />
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import http from "@/api/http";
import SellProductList from "@/components/common/SellProductList.vue";
import SellWizard from "@/components/common/SellWizard.vue";

const wizardOpen = ref(false);
const sellerId = ref<number | null>(null);
const listKey = ref(0);

async function fetchMe() {
  const { data } = await http.get("/api/auth/me");
  const id = data?.id ?? data?.user?.id;
  sellerId.value = id != null ? Number(id) : null;
}

function onPublishSuccess() {
  wizardOpen.value = false;
  // 强制刷新列表（最稳妥，避免依赖子组件内部 watch 逻辑）
  listKey.value += 1;
}

function onView(id: any) {
  console.log("view", id);
}
function onEdit(id: any) {
  console.log("edit", id);
}
function onUnlist(id: any) {
  console.log("unlist", id);
}

onMounted(() => {
  fetchMe();
});
</script>