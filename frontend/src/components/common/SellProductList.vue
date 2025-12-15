<template>
  <main class="flex-1 container mx-auto px-4 py-6">
    <!-- 标题 + 统计 + 上架按钮 -->
    <div class="mb-6 flex flex-col md:flex-row md:items-center justify-between">
      <div>
        <h2 class="text-[clamp(1.5rem,3vw,2rem)] font-bold text-neutral-700">
          我要卖机
        </h2>
        <p class="text-neutral-500 mt-1">管理您的二手电子产品销售</p>
      </div>

      <div class="mt-4 md:mt-0 flex items-center space-x-6">
        <div class="flex items-center space-x-1">
          <span class="text-neutral-500">上架中:</span>
          <span class="font-semibold text-primary">{{ stats.onSale }}</span>
        </div>
        <div class="flex items-center space-x-1">
          <span class="text-neutral-500">今日浏览:</span>
          <span class="font-semibold">{{ stats.todayViews }}</span>
        </div>
        <div class="flex items-center space-x-1">
          <span class="text-neutral-500">今日收藏:</span>
          <span class="font-semibold">{{ stats.todayFavorites }}</span>
        </div>

        <button
          class="bg-primary hover:bg-primary/90 text-white px-5 py-2.5 rounded-lg shadow-sm hover:shadow transition-all flex items-center space-x-2 font-medium"
          @click="$emit('open-wizard')"
        >
          <i class="fas fa-plus"></i>
          <span>上架商品</span>
        </button>
      </div>
    </div>

    <!-- 筛选与搜索 -->
    <div class="bg-white rounded-xl shadow-card p-4 mb-6">
      <div class="flex flex-col md:flex-row gap-4">
        <div class="flex-1">
          <div class="relative">
            <input
              v-model="localQuery"
              type="text"
              placeholder="搜索商品名称、型号..."
              class="w-full pl-10 pr-4 py-2.5 rounded-lg border border-neutral-300 focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none transition-all"
              @keyup.enter="doSearch()"
            />
            <i
              class="fas fa-search absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-400"
            ></i>
          </div>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <select
            v-model="localCategory"
            class="border border-neutral-300 rounded-lg px-4 py-2.5 focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none text-neutral-700 bg-white"
            @change="doSearch()"
          >
            <option value="">所有分类</option>
            <option value="phone">手机</option>
            <option value="laptop">笔记本电脑</option>
            <option value="tablet">平板电脑</option>
            <option value="watch">智能手表</option>
            <option value="headphones">耳机</option>
          </select>

          <select
            v-model="localBrand"
            class="border border-neutral-300 rounded-lg px-4 py-2.5 focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none text-neutral-700 bg-white"
            @change="doSearch()"
          >
            <option value="">所有品牌</option>
            <option value="apple">苹果</option>
            <option value="huawei">华为</option>
            <option value="xiaomi">小米</option>
            <option value="samsung">三星</option>
            <option value="oppo">OPPO</option>
            <option value="vivo">vivo</option>
          </select>

          <select
            v-model="localPriceRange"
            class="border border-neutral-300 rounded-lg px-4 py-2.5 focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none text-neutral-700 bg-white"
            @change="doSearch()"
          >
            <option value="">价格区间</option>
            <option value="0-500">0-500元</option>
            <option value="500-1000">500-1000元</option>
            <option value="1000-2000">1000-2000元</option>
            <option value="2000-3000">2000-3000元</option>
            <option value="3000+">3000元以上</option>
          </select>

          <select
            v-model="localTimeRange"
            class="border border-neutral-300 rounded-lg px-4 py-2.5 focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none text-neutral-700 bg-white"
            @change="doSearch()"
          >
            <option value="">上架时间</option>
            <option value="today">今天</option>
            <option value="week">本周</option>
            <option value="month">本月</option>
            <option value="quarter">本季度</option>
            <option value="year">今年</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 商品列表 -->
    <div class="bg-white rounded-xl shadow-card overflow-hidden">
      <div class="p-4 border-b border-neutral-200 flex justify-between items-center">
        <h3 class="font-semibold text-neutral-700">我的上架中商品</h3>

        <div class="flex items-center space-x-2">
          <span class="text-neutral-500 text-sm">排序:</span>
          <select
            v-model="localSort"
            class="text-sm border-none bg-transparent focus:outline-none focus:ring-0 text-neutral-600"
            @change="doSearch()"
          >
            <option value="newest">最新上架</option>
            <option value="price-asc">价格从低到高</option>
            <option value="price-desc">价格从高到低</option>
            <option value="views">浏览量最高</option>
          </select>
        </div>
      </div>

      <!-- 卡片网格 -->
      <div class="p-4">
        <div v-if="errorMsg" class="mb-3 text-sm text-red-600">{{ errorMsg }}</div>
        <div v-else-if="loading" class="mb-3 text-sm text-neutral-500">加载中...</div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <div
            v-for="p in items"
            :key="p.id"
            class="border border-neutral-200 rounded-lg overflow-hidden hover:shadow-card transition-shadow group"
          >
            <div class="relative">
              <img :src="p.image" :alt="p.title" class="w-full h-48 object-cover" />

              <div class="absolute top-2 right-2 bg-warning/90 text-white text-xs px-2 py-1 rounded">
                {{ p.conditionLabel }}
              </div>

              <div
                class="absolute inset-0 bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
              >
                <div class="flex space-x-2">
                  <button
                    class="bg-white text-neutral-700 p-2 rounded-full hover:bg-neutral-100 transition-colors"
                    title="查看详情"
                    @click="$emit('view', p.id)"
                  >
                    <i class="fas fa-eye"></i>
                  </button>

                  <button
                    class="bg-white text-neutral-700 p-2 rounded-full hover:bg-neutral-100 transition-colors"
                    title="编辑商品"
                    @click="$emit('edit', p.id)"
                  >
                    <i class="fas fa-edit"></i>
                  </button>

                  <button
                    class="bg-white text-neutral-700 p-2 rounded-full hover:bg-neutral-100 transition-colors"
                    title="下架商品"
                    @click="$emit('unlist', p.id)"
                  >
                    <i class="fas fa-arrow-down"></i>
                  </button>
                </div>
              </div>
            </div>

            <div class="p-3">
              <h4 class="font-medium text-neutral-700 line-clamp-1">{{ p.title }}</h4>

              <div class="flex items-center justify-between mt-2">
                <span class="font-bold text-danger text-lg">¥{{ formatPrice(p.price) }}</span>

                <div class="flex items-center text-neutral-500 text-sm">
                  <span class="flex items-center mr-2">
                    <i class="fas fa-eye mr-1"></i>{{ p.views }}
                  </span>
                  <span class="flex items-center">
                    <i class="fas fa-heart mr-1"></i>{{ p.favorites }}
                  </span>
                </div>
              </div>

              <p class="text-neutral-500 text-sm mt-2">上架时间: {{ p.createdAt }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div class="p-4 border-t border-neutral-200 flex justify-between items-center">
        <div class="text-neutral-500 text-sm">
          显示 {{ pagination.from }}-{{ pagination.to }} 条，共 {{ pagination.total }} 条
        </div>

        <div class="flex items-center space-x-1">
          <button
            class="w-9 h-9 flex items-center justify-center rounded border border-neutral-200 text-neutral-500 hover:border-primary hover:text-primary disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="pagination.page <= 1"
            @click="goPage(pagination.page - 1)"
          >
            <i class="fas fa-chevron-left text-xs"></i>
          </button>

          <button
            v-for="p in pagination.pages"
            :key="p"
            class="w-9 h-9 flex items-center justify-center rounded border border-neutral-200 text-neutral-500 hover:border-primary hover:text-primary"
            :class="p === pagination.page ? 'bg-primary text-white border-primary hover:text-white' : ''"
            @click="goPage(p)"
          >
            {{ p }}
          </button>

          <button
            class="w-9 h-9 flex items-center justify-center rounded border border-neutral-200 text-neutral-500 hover:border-primary hover:text-primary disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="pagination.page >= pagination.pageCount"
            @click="goPage(pagination.page + 1)"
          >
            <i class="fas fa-chevron-right text-xs"></i>
          </button>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import http from "@/api/http";

const BACKEND_ORIGIN = (import.meta as any).env?.VITE_BACKEND_ORIGIN || "http://127.0.0.1:8000";

type Stats = { onSale: number; todayViews: number; todayFavorites: number };

type ProductItem = {
  id: string | number;
  image: string;
  title: string;
  conditionLabel: string; // 95新/90新/99新...
  price: number;
  views: number;
  favorites: number;
  createdAt: string;
};

type Pagination = {
  page: number;
  pageCount: number;
  from: number;
  to: number;
  total: number;
};

const props = withDefaults(
  defineProps<{
    // 若传入 sellerId，则组件会自动请求后端：/api/market/products/?seller_id=<sellerId>
    sellerId?: number | string;

    // 兼容旧用法：父组件也可以继续传静态数据
    stats?: Stats;
    items?: ProductItem[];
    pagination?: Pagination;

    defaultFilter?: {
      q?: string;
      category?: string;
      brand?: string;
      priceRange?: string;
      timeRange?: string;
      sort?: string;
    };
  }>(),
  {
    defaultFilter: () => ({ q: "", category: "", brand: "", priceRange: "", timeRange: "", sort: "newest" }),
  }
);

const emit = defineEmits<{
  (e: "open-wizard"): void;
  (e: "search", filter: any): void;
  (e: "page", page: number): void;
  (e: "view", id: string | number): void;
  (e: "edit", id: string | number): void;
  (e: "unlist", id: string | number): void;
}>();

const localQuery = ref(props.defaultFilter?.q || "");
const localCategory = ref(props.defaultFilter?.category || "");
const localBrand = ref(props.defaultFilter?.brand || "");
const localPriceRange = ref(props.defaultFilter?.priceRange || "");
const localTimeRange = ref(props.defaultFilter?.timeRange || "");
const localSort = ref(props.defaultFilter?.sort || "newest");

const loading = ref(false);
const errorMsg = ref<string | null>(null);

const remoteItems = ref<ProductItem[]>([]);
const remoteStats = ref<Stats>({ onSale: 0, todayViews: 0, todayFavorites: 0 });
const remotePagination = ref<Pagination>({ page: 1, pageCount: 1, from: 0, to: 0, total: 0 });

function toNum(v: any, fallback = 0) {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

function pagesArray(pageCount: number) {
  const n = Math.max(1, pageCount);
  return Array.from({ length: n }, (_, i) => i + 1);
}

function mapBackendProductToItem(p: any): ProductItem {
  // 兼容后端字段：title / selling_price / main_image(or image) / grade_label / created_at
  const title = String(p?.title ?? p?.name ?? "");
  const price = toNum(p?.selling_price ?? p?.price ?? 0);

  // 图片字段尽量兼容（后端可能返回 url、相对路径或文件名）
  const rawImg =
    p?.main_image_url ??
    p?.main_image ??
    p?.image_url ??
    p?.image ??
    p?.image_name ??
    "";

  const image = typeof rawImg === "string" && rawImg
    ? (
        // 已是完整 URL（http(s)、blob、data）直接使用
        /^(https?:)?\/\//.test(rawImg) || rawImg.startsWith("blob:") || rawImg.startsWith("data:")
          ? rawImg
          : (
              // rawImg 可能是文件名：0ba15....jpg -> /media/products/<name>
              (() => {
                const path = rawImg.includes("/")
                  ? (rawImg.startsWith("/") ? rawImg : `/${rawImg}`)
                  : `/media/products/${rawImg}`;

                // media 相对路径需要指向后端域名（开发环境前端为 :5173，后端为 :8000）
                if (path.startsWith("/media/")) {
                  return `${BACKEND_ORIGIN}${path}`;
                }
                return path;
              })()
            )
      )
    : "";

  const conditionLabel = String(p?.grade_label ?? p?.condition_label ?? p?.conditionLabel ?? "");
  const createdAt = String(p?.created_at ?? p?.createdAt ?? p?.created_time ?? "");

  return {
    id: p?.id ?? p?.product_id ?? p?.pk,
    image,
    title,
    conditionLabel,
    price,
    views: toNum(p?.views ?? p?.view_count ?? 0),
    favorites: toNum(p?.favorites ?? p?.favorite_count ?? 0),
    createdAt,
  };
}

async function fetchProducts(page = 1) {
  if (!useRemote.value) {
    // 未提供 sellerId prop 时，不强制走接口（兼容旧传参模式）
    return;
  }
  if (props.sellerId == null || String(props.sellerId).trim() === "") {
    // remote 模式但 sellerId 还没拿到
    remoteItems.value = [];
    remoteStats.value = { onSale: 0, todayViews: 0, todayFavorites: 0 };
    remotePagination.value = { page: 1, pageCount: 1, from: 0, to: 0, total: 0 } as any;
    return;
  }

  loading.value = true;
  errorMsg.value = null;

  const params: any = {
    seller_id: String(props.sellerId).trim(),
    q: localQuery.value || undefined,
    sort: localSort.value || undefined,
    page,
    // 兼容不同分页参数命名
    limit: 12,
    page_size: 12,
  };

  try {
    const { data } = await http.get("/api/market/products/", { params });

    // 兼容两种返回：分页对象 or 数组
    const list = Array.isArray(data)
      ? data
      : Array.isArray(data?.results)
        ? data.results
        : [];

    const total = toNum(data?.count ?? data?.total ?? list.length, list.length);
    const pageSize = 12;
    const pageCount = Math.max(1, Math.ceil(total / pageSize));

    remoteItems.value = list.map(mapBackendProductToItem);
    remoteStats.value = {
      onSale: total,
      todayViews: 0,
      todayFavorites: 0,
    };

    const from = total === 0 ? 0 : (page - 1) * pageSize + 1;
    const to = Math.min(total, page * pageSize);

    remotePagination.value = {
      page,
      pageCount,
      from,
      to,
      total,
      // 供模板 v-for 使用
      pages: pagesArray(pageCount) as any,
    } as any;
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail || e?.message || "加载商品失败";
    remoteItems.value = [];
    remoteStats.value = { onSale: 0, todayViews: 0, todayFavorites: 0 };
    remotePagination.value = { page: 1, pageCount: 1, from: 0, to: 0, total: 0 };
  } finally {
    loading.value = false;
  }
}

function doSearch() {
  const filter = buildFilter();
  // 保留原来的向父组件通知
  emit("search", filter);
  fetchProducts(1);
}

function goPage(p: number) {
  emit("page", p);
  fetchProducts(p);
}

onMounted(() => {
  fetchProducts(1);
});

watch(
  () => props.sellerId,
  () => {
    fetchProducts(1);
  }
);

function buildFilter() {
  return {
    q: localQuery.value,
    category: localCategory.value,
    brand: localBrand.value,
    priceRange: localPriceRange.value,
    timeRange: localTimeRange.value,
    sort: localSort.value,
  };
}

function formatPrice(n: number) {
  // 模仿 a.html 的 “¥5,299” 样式
  return n.toLocaleString("zh-CN");
}

const useRemote = computed(() => props.sellerId !== undefined);

const stats = computed<Stats>(() => {
  if (useRemote.value) return remoteStats.value;
  return (props.stats as Stats) ?? { onSale: 0, todayViews: 0, todayFavorites: 0 };
});

const items = computed<ProductItem[]>(() => {
  if (useRemote.value) return remoteItems.value;
  return (props.items as ProductItem[]) ?? [];
});

const pagination = computed(() => {
  if (!useRemote.value) {
    const p: any = (props.pagination as any) ?? { page: 1, pageCount: 1, from: 0, to: 0, total: 0, pages: [1] };
    if (!p.pages) p.pages = pagesArray(p.pageCount ?? 1);
    return p;
  }
  const p: any = remotePagination.value as any;
  if (!p.pages) p.pages = pagesArray(p.pageCount);
  return p;
});
</script>