<template>
  <SellProductList
    :stats="stats"
    :items="items"
    :pagination="pagination"
    @open-wizard="wizardOpen = true"
    @search="onSearch"
    @page="onPage"
    @view="onView"
    @edit="onEdit"
    @unlist="onUnlist"
  />

  <SellWizard
    :open="wizardOpen"
    @close="wizardOpen = false"
    @success="refreshList"
  />
</template>

<script setup lang="ts">
import { ref } from "vue";
import SellProductList from "@/components/common/SellProductList.vue";
import SellWizard from "@/components/common/SellWizard.vue";

const wizardOpen = ref(false);

const stats = ref({ onSale: 12, todayViews: 86, todayFavorites: 15 });

const items = ref([
  {
    id: 1,
    image: "https://design.gemcoder.com/staticResource/echoAiSystemImages/877eae20b4cd21fa5cfbb0e03eedd327.png",
    title: "iPhone 13 Pro 256GB 星光色",
    conditionLabel: "95新",
    price: 5299,
    views: 128,
    favorites: 24,
    createdAt: "2023-06-15",
  },
  // ...你后面用 API 替换
]);

const pagination = ref({ page: 1, pageCount: 2, from: 1, to: 6, total: 12, pages: [1, 2] });

function refreshList() {
  // TODO: 调用后端刷新 “上架中列表 + 统计”
}

function onSearch(filter: any) {
  // TODO: 带 filter 调接口
  console.log("search:", filter);
}

function onPage(page: number) {
  pagination.value.page = page;
  // TODO: 调接口拉页
}

function onView(id: any) { console.log("view", id); }
function onEdit(id: any) { console.log("edit", id); }
function onUnlist(id: any) { console.log("unlist", id); }
</script>