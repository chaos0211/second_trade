<template>
  <DefaultLayout>
    <div class="animate-fade-in">
      <!-- 标题区 -->
      <div class="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
        <div>
          <h1 class="text-[clamp(1.5rem,3vw,2rem)] font-bold text-dark">市场大厅</h1>
          <p class="text-dark-2 mt-1">发现优质二手电子设备，安全交易有保障</p>
        </div>
        <div class="mt-4 md:mt-0 flex space-x-3">
          <button class="px-4 py-2 border border-primary text-primary rounded-lg hover:bg-primary/5 transition-colors">
            <i class="fas fa-filter mr-2"></i>高级筛选
          </button>
          <button class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors shadow-sm hover:shadow">
            <i class="fas fa-plus mr-2"></i>我要卖机
          </button>
        </div>
      </div>

      <FilterBar v-model="filters" />

      <ProductGrid :items="products" @open="openProduct" />

      <Pagination class="mt-8" />

      <ProductModal v-model:open="modalOpen" :product="activeProduct" />
    </div>
  </DefaultLayout>
</template>

<script setup lang="ts">
import { ref } from "vue";
import DefaultLayout from "@/layouts/DefaultLayout.vue";
import FilterBar from "@/components/marketplace/FilterBar.vue";
import ProductGrid from "@/components/marketplace/ProductGrid.vue";
import ProductModal from "@/components/common/ProductModal.vue";
import Pagination from "@/components/common/Pagination.vue";

type Product = {
  id: number;
  title: string;
  brandText: string;
  rating: string;
  conditionTag: string;
  conditionColorClass: string;
  cover: string;
  desc: string;
  price: string;
  oldPrice: string;
  favCount: string;
};

const filters = ref({
  brand: "",
  condition: "",
  priceRange: "",
  sort: "recommend",
});

const products = ref<Product[]>([
  {
    id: 1,
    title: "iPhone 13 Pro 256GB 星光色",
    brandText: "Apple",
    rating: "4.9",
    conditionTag: "95新",
    conditionColorClass: "bg-success/90",
    cover: "https://design.gemcoder.com/staticResource/echoAiSystemImages/4007bd1ba5aaa4f94a23d259b8825262.png",
    desc: "电池健康：92%，无划痕，原装配件齐全，保修期至2023年12月",
    price: "￥5,299",
    oldPrice: "￥7,999",
    favCount: "128",
  },
  // …其余卡片按你原 HTML 填充
]);

const modalOpen = ref(false);
const activeProduct = ref<Product | null>(null);

function openProduct(p: Product) {
  activeProduct.value = p;
  modalOpen.value = true;
}
</script>