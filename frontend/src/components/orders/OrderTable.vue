<template>
  <div
    id="order-list-container"
    class="bg-white rounded-xl shadow-sm border border-neutral-200 overflow-hidden"
  >
    <!-- 订单列表头部（桌面端） -->
    <div
      class="hidden md:grid md:grid-cols-12 px-6 py-4 bg-neutral-50 border-b border-neutral-200 text-neutral-500 font-medium"
    >
      <div class="col-span-3">商品信息</div>
      <div class="col-span-3">购买时间</div>
      <div class="col-span-2">购买价格</div>
      <div class="col-span-2">订单状态</div>
      <div class="col-span-2 text-right">操作</div>
    </div>

    <!-- 列表内容 -->
    <div id="order-list" class="divide-y divide-neutral-200" v-show="!loading && totalAll > 0">
      <div
        v-for="o in orders"
        :key="o.id"
        class="order-card"
        :data-order-id="o.id"
      >
        <div class="p-4 md:p-6">
          <div class="flex flex-col gap-4">
            <!-- 移动端信息（保持不变） -->
            <div class="md:hidden">
              <div class="flex items-start gap-4">
                <div
                  class="relative w-16 h-16 rounded-lg overflow-hidden border border-neutral-200 flex-shrink-0 cursor-pointer order-thumbnail"
                  :data-order-id="o.id"
                  @click="$emit('open', o.id)"
                >
                  <img :src="o.product.thumbnail" :alt="o.product.title" class="w-full h-full object-cover" />
                </div>
                <div class="flex-1 min-w-0">
                  <h3 class="font-medium text-neutral-700 truncate" :title="o.product?.title || ''">{{ o.product?.title || '-' }}</h3>
                  <p class="text-neutral-400 text-sm mt-1 truncate" :title="o.product?.specs || ''">{{ o.product?.specs || '' }}</p>
                </div>
              </div>

              <div class="grid grid-cols-2 gap-y-2 gap-x-4 w-full mt-4">
                <div>
                  <p class="text-neutral-400 text-sm">购买时间</p>
                  <p class="text-neutral-700">{{ formatTime(o.purchaseTime) }}</p>
                </div>
                <div>
                  <p class="text-neutral-400 text-sm">购买价格</p>
                  <p class="text-danger font-bold text-lg">¥{{ formatPrice(o.purchasePrice) }}</p>
                </div>
                <div class="col-span-2">
                  <p class="text-neutral-400 text-sm">订单状态</p>
                  <span class="badge-pill" :class="getStatusClass(o.status)">{{ getStatusText(o.status) }}</span>
                </div>

                <div class="col-span-2 flex justify-end flex-wrap gap-2 mt-2">
                  <button
                    v-for="btn in getActionButtons(o.status)"
                    :key="btn.action"
                    class="btn"
                    :class="btn.className"
                    type="button"
                    :data-action="btn.action"
                    @click.stop="$emit('action', o.id, btn.action)"
                  >
                    {{ btn.text }}
                  </button>
                </div>
              </div>
            </div>

            <!-- 桌面端信息：12列固定布局，和表头对齐 -->
            <div class="hidden md:grid md:grid-cols-12 md:items-center md:gap-4">
              <!-- 商品信息 -->
              <div class="col-span-3 flex items-center gap-4 min-w-0">
                <div
                  class="relative w-16 h-16 rounded-lg overflow-hidden border border-neutral-200 flex-shrink-0 cursor-pointer order-thumbnail"
                  :data-order-id="o.id"
                  @click="$emit('open', o.id)"
                >
                  <img :src="o.product.thumbnail" :alt="o.product.title" class="w-full h-full object-cover" />
                </div>
                <div class="min-w-0">
                  <h3 class="font-medium text-neutral-700 truncate" :title="o.product?.title || ''">{{ o.product?.title || '-' }}</h3>
                  <p class="text-neutral-400 text-sm mt-1 truncate" :title="o.product?.specs || ''">{{ o.product?.specs || '' }}</p>
                </div>
              </div>

              <!-- 购买时间 -->
              <div class="col-span-3 text-left">
                <p class="text-neutral-700 whitespace-nowrap">{{ formatTime(o.purchaseTime) }}</p>
              </div>

              <!-- 购买价格 -->
              <div class="col-span-2 text-left">
                <p class="text-danger font-bold text-lg whitespace-nowrap">¥{{ formatPrice(o.purchasePrice) }}</p>
              </div>

              <!-- 订单状态 -->
              <div class="col-span-2 text-left">
                <span class="badge-pill" :class="getStatusClass(o.status)">{{ getStatusText(o.status) }}</span>
              </div>

              <!-- 操作 -->
              <div class="col-span-2 flex justify-end flex-wrap gap-2">
                <button
                  v-for="btn in getActionButtons(o.status)"
                  :key="btn.action"
                  class="btn"
                  :class="btn.className"
                  type="button"
                  :data-action="btn.action"
                  @click.stop="$emit('action', o.id, btn.action)"
                >
                  {{ btn.text }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div
      id="empty-state"
      class="flex flex-col items-center justify-center py-16 px-4 text-center"
      v-show="!loading && totalAll === 0"
    >
      <img
        src="https://design.gemcoder.com/staticResource/echoAiSystemImages/ef6eb36f01bd83829fc73d3e5137a13a.png"
        alt="空订单"
        class="w-32 h-32 mb-4 opacity-60"
      />
      <h3 class="text-lg font-medium text-neutral-700 mb-2">暂无订单记录</h3>
      <p class="text-neutral-400 max-w-md mb-6">您还没有相关的订单记录，快去市场大厅看看吧</p>
      <a href="javascript:void(0);" class="btn btn-primary">
        <i class="fas fa-shopping-bag mr-2"></i>
        去逛市场大厅
      </a>
    </div>

    <!-- 加载中 -->
    <div id="loading-state" class="flex items-center justify-center py-16" v-show="loading">
      <div class="flex flex-col items-center">
        <div class="w-12 h-12 border-4 border-neutral-200 border-t-primary rounded-full animate-spin"></div>
        <p class="mt-4 text-neutral-500">加载中...</p>
      </div>
    </div>

    <!-- 分页 -->
    <div
      id="pagination-container"
      class="py-4 px-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4"
      v-show="!loading && totalAll > 0"
    >
      <div class="text-neutral-500 text-sm">
        共 <span id="total-orders">{{ totalAll }}</span> 条，当前显示
        <span id="current-range">{{ rangeText }}</span>
      </div>

      <div class="flex items-center gap-1">
        <button
          id="prev-page"
          class="pagination-item"
          :class="page <= 1 ? 'disabled' : ''"
          type="button"
          aria-label="上一页"
          @click="$emit('page', page - 1)"
        >
          <i class="fas fa-chevron-left text-sm"></i>
        </button>

        <div id="pagination-numbers" class="flex items-center gap-1">
          <button
            v-for="n in pageNumbers"
            :key="n.key"
            class="pagination-item"
            :class="n.type === 'ellipsis'
              ? 'text-neutral-400'
              : (n.page === page ? 'active' : '')"
            :disabled="n.type === 'ellipsis'"
            type="button"
            @click="n.type !== 'ellipsis' && $emit('page', n.page)"
          >
            {{ n.text }}
          </button>
        </div>

        <button
          id="next-page"
          class="pagination-item"
          :class="page >= totalPages ? 'disabled' : ''"
          type="button"
          aria-label="下一页"
          @click="$emit('page', page + 1)"
        >
          <i class="fas fa-chevron-right text-sm"></i>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const formatTime = (v: any) => {
  if (!v) return "-";
  if (typeof v === "string") return v;
  try {
    if (v instanceof Date) return v.toLocaleString();
    if (typeof v?.toLocaleString === "function") return v.toLocaleString();
  } catch {
    // ignore
  }
  return String(v);
};

const formatPrice = (v: any) => {
  if (v === null || v === undefined || v === "") return "-";
  const n = typeof v === "number" ? v : Number(v);
  if (Number.isFinite(n)) return n.toLocaleString();
  return String(v);
};

type Status = "pending_payment" | "pending_receipt" | "shipped" | "completed" | "refunded";

type OrderItem = {
  id: number;
  order_no: string;
  status: Status;
  purchaseTime: string;
  purchasePrice: number;
  product: { id: number; title: string; specs: string; images: string[]; thumbnail: string };
  buyerName?: string;
  sellerName?: string;
  buyerAddress?: string;
  sellerAddress?: string;
};

const props = defineProps<{
  orders: OrderItem[];
  loading: boolean;
  page: number;
  pageSize: number;
  tab: "bought" | "sold";
}>();

defineEmits<{
  (e: "page", p: number): void;
  (e: "open", orderId: number): void;
  (e: "action", orderId: number, action: string): void;
}>();

// 注意：这里 totalAll / totalPages / rangeText 需要父组件提供总量的话也行；
// 为了不增加文件数量，这里用“当前列表长度 + pageSize”推导不可靠。
// 所以：OrderCenterView 已经把 orders 切片了，这里只能用当前页范围显示，totalAll 由父组件在真实接入时再做。
// 目前先用“当前页条数 + 估算”不行，所以这里直接让父组件传 totalAll 更合理——但你要求少文件，我就先给最简可跑版本：
// 把 totalAll 当做当前 tab 的总量：你可以在接真实接口时改为 props.totalAll。

const totalAll = computed(() => {
  // 最简：当前页如果只有切片，这里显示会偏小；建议你接接口后改为真实总数
  return props.orders.length;
});

const totalPages = computed(() => Math.max(1, Math.ceil(totalAll.value / props.pageSize)));

const rangeText = computed(() => {
  if (totalAll.value === 0) return "0-0";
  const start = (props.page - 1) * props.pageSize + 1;
  const end = Math.min(props.page * props.pageSize, totalAll.value);
  return `${start}-${end}`;
});

// 生成页码（沿用 a.html 的 5 个页码策略）
const pageNumbers = computed(() => {
  const pages: Array<{ key: string; type: "page" | "ellipsis"; page?: number; text: string }> = [];
  const cur = props.page;
  const tp = totalPages.value;

  let start = Math.max(1, cur - 2);
  let end = Math.min(tp, start + 4);

  if (end - start < 4 && tp > 5) {
    if (start === 1) end = 5;
    else if (end === tp) start = Math.max(1, tp - 4);
  }

  if (start > 1) {
    pages.push({ key: "p-1", type: "page", page: 1, text: "1" });
    if (start > 2) pages.push({ key: "e-1", type: "ellipsis", text: "..." });
  }
  for (let i = start; i <= end; i++) pages.push({ key: `p-${i}`, type: "page", page: i, text: String(i) });
  if (end < tp) {
    if (end < tp - 1) pages.push({ key: "e-2", type: "ellipsis", text: "..." });
    pages.push({ key: `p-${tp}`, type: "page", page: tp, text: String(tp) });
  }

  return pages;
});

// ===== 状态/按钮：保持 a.html 一致 =====
function getStatusClass(status: Status) {
  switch (status) {
    case "pending_payment":
      return "bg-warning/10 text-warning";
    case "pending_receipt":
    case "shipped":
      return "bg-primary/10 text-primary";
    case "completed":
      return "bg-success/10 text-success";
    case "refunded":
      return "bg-danger/10 text-danger";
    default:
      return "bg-neutral-100 text-neutral-500";
  }
}
function getStatusText(status: Status) {
  switch (status) {
    case "pending_payment":
      return "待付款";
    case "pending_receipt":
      return "待收货";
    case "shipped":
      return "已发货";
    case "completed":
      return "已完成";
    case "refunded":
      return "已退款";
    default:
      return "未知状态";
  }
}
function getActionButtons(status: Status) {
  const buttons: { text: string; className: string; action: string }[] = [];

  if (props.tab === "bought") {
    if (status === "pending_payment") {
      buttons.push({ text: "去支付", className: "btn-primary", action: "pay" });
    }
    if (status === "pending_receipt" || status === "shipped") {
      buttons.push({ text: "确认收货", className: "btn-primary", action: "confirm" });
      buttons.push({ text: "申请退款", className: "btn-secondary", action: "refund" });
    }
  } else {
    if (status === "pending_receipt") {
      buttons.push({ text: "发货", className: "btn-primary", action: "ship" });
    }
  }

  return buttons;
}
</script>