<template>
  <div class="animate-fade-in">
    <!-- 分类选择页 -->
    <div v-if="!enteredCategoryId">
      <CategoryPicker
        :categories="categories"
        title="选择电子产品分类"
        subtitle="先选择分类，再点击进入查看该分类下的商品"
        enter-text="点击进入"
        @select="onSelectCategory"
        @enter="onEnterCategory"
      />
    </div>

    <!-- 商品列表页 -->
    <div v-else>
      <!-- 标题区 -->
      <div class="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
        <div>
          <h1 class="text-[clamp(1.5rem,3vw,2rem)] font-bold text-dark">二手市场大厅</h1>
          <div class="mt-2 flex items-center gap-2">
            <button
              type="button"
              class="px-3 py-1.5 rounded-lg border border-light-2 text-dark-2 hover:bg-gray-50 transition"
              @click="backToCategories"
            >
              返回分类
            </button>
            <span class="text-sm text-slate-500">
              当前分类：<span class="font-semibold text-slate-700">{{ selectedCategoryName }}</span>
            </span>
          </div>
        </div>
      </div>

      <FilterBar v-model="filters" />

      <div v-if="errorMsg" class="mb-3 text-sm text-red-600">{{ errorMsg }}</div>
      <div v-else-if="loading" class="mb-3 text-sm text-neutral-500">加载中...</div>

      <ProductGrid :items="products" @open="openProduct" />

      <Pagination class="mt-8" />

      <ProductModal v-model:open="modalOpen" :product="activeProduct" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import http from "@/api/http";
import FilterBar from "@/components/marketplace/FilterBar.vue";
import ProductGrid from "@/components/marketplace/ProductGrid.vue";
import ProductModal from "@/components/common/ProductModal.vue";
import Pagination from "@/components/common/Pagination.vue";

import CategoryPicker from "@/components/common/CategoryPicker.vue";

const BACKEND_ORIGIN = (import.meta as any).env?.VITE_BACKEND_ORIGIN || "http://127.0.0.1:8000";

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

type Category = {
  id: number;
  name: string;
  code?: string;
};

const categories = ref<Category[]>([]);
const pendingCategoryId = ref<number | null>(null);
const enteredCategoryId = ref<number | null>(null);

const filters = ref({
  brand: "",
  condition: "",
  priceRange: "",
  sort: "recommend",
});

const products = ref<Product[]>([]);
const loading = ref(false);
const errorMsg = ref<string | null>(null);

const modalOpen = ref(false);
const activeProduct = ref<Product | null>(null);

const selectedCategoryName = computed(() => {
  const id = enteredCategoryId.value;
  if (id == null) return "";
  const c = categories.value.find((x) => Number(x.id) === Number(id));
  return c?.name || `类目#${id}`;
});

async function fetchCategories() {
  try {
    const { data } = await http.get("/api/market/categories/");
    categories.value = Array.isArray(data) ? data : [];
  } catch {
    categories.value = [];
  }
}

function formatMoney(v: any) {
  const n = Number(v);
  if (!Number.isFinite(n)) return "";
  return `￥${n.toLocaleString("zh-CN", { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
}

function toCoverUrl(raw: any) {
  const s = typeof raw === "string" ? raw : "";
  if (!s) return "";
  if (/^(https?:)?\/\//.test(s) || s.startsWith("blob:") || s.startsWith("data:")) return s;
  // 后端通常返回 /media/products/xxx.jpg
  if (s.startsWith("/media/")) return `${BACKEND_ORIGIN}${s}`;
  if (s.startsWith("/")) return s;
  return `${BACKEND_ORIGIN}/media/products/${s}`;
}

function mapBackendToCard(p: any): Product {
  const title = String(p?.title ?? "");
  const conditionTag = String(p?.grade_label ?? p?.condition_label ?? "");

  // 兼容：后端可能返回 main_image (/media/..)，或 image_name (文件名)
  const cover = toCoverUrl(p?.main_image ?? p?.main_image_url ?? p?.image_name ?? "");

  const price = formatMoney(p?.selling_price ?? p?.price);
  const oldPrice = formatMoney(p?.original_price ?? p?.old_price);

  const favCount = String(p?.favorite_count ?? p?.favorites ?? 0);

  // 简短描述：market_tag / created_at / defects 等按你现有字段尽量拼
  const tag = String(p?.market_tag ?? "");
  const createdAt = String(p?.created_at ?? "");
  const descParts = [tag, createdAt].filter((x) => x && x !== "None");

  return {
    id: Number(p?.id ?? p?.product_id ?? 0),
    title,
    brandText: String(p?.brand_text ?? p?.brand ?? ""),
    rating: String(p?.value_score ?? p?.rating ?? ""),
    conditionTag: conditionTag || "",
    conditionColorClass: "bg-success/90",
    cover,
    desc: descParts.join(" · "),
    price,
    oldPrice,
    favCount,
  };
}

async function fetchMarketProducts() {
  loading.value = true;
  errorMsg.value = null;

  // FilterBar 的 filters 结构沿用现有（brand/condition/priceRange/sort）
  const params: any = {
    brand: filters.value.brand || undefined,
    condition: filters.value.condition || undefined,
    priceRange: filters.value.priceRange || undefined,
    sort: filters.value.sort || undefined,
    // 你后端如果支持分页，可在此添加 page/limit
    limit: 24,
    page_size: 24,
    category_id: enteredCategoryId.value || undefined,
  };

  try {
    const { data } = await http.get("/api/market/products/", { params });
    const list = Array.isArray(data) ? data : Array.isArray(data?.results) ? data.results : [];
    products.value = list.map(mapBackendToCard);
  } catch (e: any) {
    products.value = [];
    errorMsg.value = e?.response?.data?.detail || e?.message || "加载市场商品失败";
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  fetchCategories();
});

watch(
  filters,
  () => {
    if (enteredCategoryId.value) fetchMarketProducts();
  },
  { deep: true }
);

function openProduct(p: Product) {
  activeProduct.value = p;
  modalOpen.value = true;
}

function onSelectCategory(categoryId: number | string) {
  // 原型要求：点卡片只高亮，不切页面
  const id = Number(categoryId);
  pendingCategoryId.value = Number.isFinite(id) ? id : null;
}

function onEnterCategory(categoryId?: number | string) {
  // 原型要求：点击“点击进入”才进入列表页
  // 兼容：有些实现的 @enter 可能不带参数，此时用已选中的 pendingCategoryId
  const id = categoryId != null ? Number(categoryId) : pendingCategoryId.value;
  if (id == null || !Number.isFinite(Number(id))) {
    // 未选择分类时不进入
    return;
  }
  enteredCategoryId.value = Number(id);
  // 进入后按分类拉取商品
  fetchMarketProducts();
}

function backToCategories() {
  enteredCategoryId.value = null;
  pendingCategoryId.value = null;
  products.value = [];
  errorMsg.value = null;
}
</script>