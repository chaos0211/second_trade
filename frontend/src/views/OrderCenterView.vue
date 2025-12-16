<template>
  <main class="flex-grow container mx-auto px-4 py-8">
    <div id="order-center-page" class="space-y-6">
      <!-- 标题 -->
      <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 class="text-[clamp(1.5rem,3vw,2rem)] font-bold text-neutral-700">订单中心</h1>
          <p class="text-neutral-400 mt-1">管理您的所有交易订单</p>
        </div>
      </div>

      <!-- 标签页 -->
      <div class="bg-white rounded-xl shadow-sm border border-neutral-200">
        <div class="flex border-b border-neutral-200">
          <button
            id="bought-tab"
            class="py-4 px-6 border-b-2 text-lg transition-all duration-200"
            :class="tab === 'bought' ? 'tab-active' : 'border-transparent text-neutral-500'"
            type="button"
            @click="switchTab('bought')"
          >
            我买到的
          </button>
          <button
            id="sold-tab"
            class="py-4 px-6 border-b-2 text-lg transition-all duration-200"
            :class="tab === 'sold' ? 'tab-active' : 'border-transparent text-neutral-500'"
            type="button"
            @click="switchTab('sold')"
          >
            我卖出的
          </button>
        </div>
      </div>

      <!-- 列表 -->
      <OrderTable
        :orders="currentOrders"
        :loading="loading"
        :page="page"
        :page-size="pageSize"
        :tab="tab"
        @page="changePage"
        @open="openOrderDetail"
        @action="handleOrderAction"
      />

      <!-- 详情弹窗 -->
      <OrderDetailModal
        :open="detailOpen"
        :order="detailOrder"
        :actions="getActionButtons(detailOrder?.status)"
        :status-text="getStatusText(detailOrder?.status)"
        :status-class="getStatusClass(detailOrder?.status)"
        @close="closeModal"
        @action="handleOrderAction(detailOrder?.id, $event)"
      />

      <!-- 支付确认弹窗 -->
      <div v-if="payConfirmOpen" class="fixed inset-0 z-50 flex items-center justify-center">
        <div class="absolute inset-0 bg-black/40" @click="closePayConfirm"></div>
        <div class="relative w-[92vw] max-w-md bg-white rounded-xl shadow-lg border border-neutral-200 p-6">
          <h3 class="text-lg font-semibold text-neutral-800">是否确认支付订单</h3>
          <p class="mt-2 text-neutral-600 break-all">
            {{ payTargetOrder?.order_no || "" }}
          </p>

          <div class="mt-6 flex justify-end gap-3">
            <button type="button" class="px-4 py-2 rounded-lg border border-neutral-300 text-neutral-700 hover:bg-neutral-50" @click="closePayConfirm">
              取消
            </button>
            <button type="button" class="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary/90" @click="confirmPay">
              确认
            </button>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import OrderTable from "@/components/orders/OrderTable.vue";
import OrderDetailModal from "@/components/orders/OrderDetailModal.vue";
import {
  listBuyerOrders,
  listSellerOrders,
  getOrderDetail,
  payOrder,
  shipOrder,
  confirmReceipt,
  refundOrder,
} from "@/api/market";

type Status = "pending_payment" | "pending_shipment" | "pending_receipt" | "shipped" | "completed" | "refunded" | "received";
type Tab = "bought" | "sold";

type OrderItem = {
  id: number;
  order_no: string;
  status: Status;
  statusView?: string;
  // purchase info
  purchaseTime: string;
  purchasePrice: number;
  // product summary
  product: {
    id: number;
    title: string;
    specs: string;
    images: string[];
    thumbnail: string;
  };
  // parties
  buyerName?: string;
  sellerName?: string;
  buyerAddress?: string;
  sellerAddress?: string;
};

const tab = ref<Tab>("bought");
const page = ref(1);
const pageSize = ref(10);
const loading = ref(true);
const allOrders = ref<Record<Tab, OrderItem[]>>({
  bought: [],
  sold: [],
});

const detailOpen = ref(false);
const detailOrder = ref<OrderItem | null>(null);

const payConfirmOpen = ref(false);
const payTargetOrder = ref<OrderItem | null>(null);

function openPayConfirm(orderId: number) {
  const found = currentOrdersAll.value.find((o) => o.id === orderId) || null;
  payTargetOrder.value = found;
  payConfirmOpen.value = true;
  document.body.style.overflow = "hidden";
}

function closePayConfirm() {
  payConfirmOpen.value = false;
  payTargetOrder.value = null;
  document.body.style.overflow = "";
}

async function confirmPay() {
  if (!payTargetOrder.value?.id) return;
  try {
    await payOrder(payTargetOrder.value.id);
    closePayConfirm();
    await loadOrders();
  } catch (e: any) {
    alert(e?.message || "支付失败");
  }
}

function statusToText(status?: string) {
  switch (status) {
    case "pending_payment":
      return "待付款";
    case "pending_shipment":
      return "待发货";
    case "pending_receipt":
      return "待收货";
    case "shipped":
      return "已发货";
    case "completed":
      return "已完成";
    case "refunded":
      return "已取消";
    case "received":
      return "已完成";
    default:
      return "未知状态";
  }
}

const API_ORIGIN = (import.meta as any).env?.VITE_API_ORIGIN || "http://127.0.0.1:8000";

const toAbsUrl = (u: string) => {
  if (!u) return "";
  if (u.startsWith("http://") || u.startsWith("https://")) return u;
  if (u.startsWith("/")) return `${API_ORIGIN}${u}`;
  return `${API_ORIGIN}/${u}`;
};

function toPurchaseTime(o: any) {
  // Prefer paid time if present, otherwise created_at
  return o?.paid_at || o?.payment_time || o?.created_at || "";
}

function toPrice(o: any) {
  const v = o?.product_selling_price ?? o?.product?.selling_price ?? o?.price ?? 0;
  const n = typeof v === "string" ? Number(v) : v;
  return Number.isFinite(n) ? n : 0;
}

function toSpecs(o: any) {
  // Keep it short; table cell will truncate.
  const parts: string[] = [];
  if (o?.grade_label) parts.push(`成色：${o.grade_label}`);
  if (o?.years_used !== undefined && o?.years_used !== null) parts.push(`使用：${o.years_used}年`);
  if (o?.category_name) parts.push(o.category_name);
  if (o?.device_model_name) parts.push(o.device_model_name);
  return parts.join(" | ");
}

function normalizeOrder(o: any): OrderItem {
  const img = o?.product_main_image || o?.main_image || o?.product?.main_image || "";
  const thumb = img ? toAbsUrl(img) : "";
  const title = o?.product_title || o?.product?.title || "";

  return {
    id: Number(o?.id),
    order_no: String(o?.order_no ?? ""),
    status: (o?.status ?? "") as Status,
    statusView: (o?.status_view ? String(o.status_view) : statusToText(o?.status)) as string,
    purchaseTime: toPurchaseTime(o),
    purchasePrice: toPrice(o),
    product: {
      id: Number(o?.product_id ?? o?.product?.id),
      title,
      specs: toSpecs(o),
      images: thumb ? [thumb] : [],
      thumbnail: thumb,
    },
    buyerName: o?.buyer_name,
    sellerName: o?.seller_name,
    buyerAddress: o?.buyer_address,
    sellerAddress: o?.seller_address,
  };
}

async function loadOrders() {
  loading.value = true;
  try {
    const data = tab.value === "bought" ? await listBuyerOrders() : await listSellerOrders();
    const normalized = (Array.isArray(data) ? data : []).map((o: any) => normalizeOrder(o));
    allOrders.value[tab.value] = normalized;
  } finally {
    loading.value = false;
  }
}

onMounted(loadOrders);

const currentOrdersAll = computed(() => allOrders.value[tab.value] || []);
const totalPages = computed(() => Math.max(1, Math.ceil(currentOrdersAll.value.length / pageSize.value)));

const currentOrders = computed(() => {
  const start = (page.value - 1) * pageSize.value;
  const end = Math.min(start + pageSize.value, currentOrdersAll.value.length);
  return currentOrdersAll.value.slice(start, end);
});

function switchTab(t: Tab) {
  if (tab.value === t) return;
  tab.value = t;
  page.value = 1;
  loadOrders();
}

function changePage(p: number) {
  if (p < 1 || p > totalPages.value || p === page.value) return;
  page.value = p;
}

async function openOrderDetail(orderId: number) {
  const found = currentOrdersAll.value.find((o) => o.id === orderId) || null;
  detailOrder.value = found;
  detailOpen.value = true;
  document.body.style.overflow = "hidden";

  try {
    const detail = await getOrderDetail(orderId);
    // merge detail fields back
    const merged = normalizeOrder({ ...(detail as any), ...(detailOrder.value as any) });
    detailOrder.value = merged;
  } catch {
    // ignore; keep summary
  }
}

function closeModal() {
  detailOpen.value = false;
  detailOrder.value = null;
  if (!payConfirmOpen.value) document.body.style.overflow = "";
}

// ====== 状态工具：保持与 a.html 一致 ======
function getStatusClass(status?: Status) {
  switch (status) {
    case "pending_payment":
      return "bg-warning/10 text-warning";
    case "pending_shipment":
      return "bg-primary/10 text-primary";
    case "pending_receipt":
      return "bg-primary/10 text-primary";
    case "shipped":
      return "bg-primary/10 text-primary";
    case "completed":
      return "bg-success/10 text-success";
    case "refunded":
      return "bg-danger/10 text-danger";
    case "received":
      return "bg-success/10 text-success";
    default:
      return "bg-neutral-100 text-neutral-500";
  }
}

function getStatusText(status?: Status) {
  // Prefer backend-provided label for buyer/seller perspective.
  const anyOrder = (detailOrder.value as any) || null;
  if (anyOrder?.statusView) return anyOrder.statusView;
  return statusToText(status);
}

function getActionButtons(status?: Status) {
  const buttons: { text: string; className: string; action: string }[] = [];

  if (!status) return buttons;

  if (tab.value === "bought") {
    // buyer actions

    if (status === "pending_receipt" || status === "shipped") {
      buttons.push({ text: "确认收货", className: "btn-primary", action: "confirm" });
      buttons.push({ text: "取消订单", className: "btn-secondary", action: "refund" });
    }
  } else {
    // seller actions
    if (status === "pending_shipment") {
      buttons.push({ text: "发货", className: "px-3 py-2 rounded-lg bg-primary text-white hover:bg-primary/90", action: "ship" });
    }
  }

  return buttons;
}

async function handleOrderAction(orderId: number | undefined, action: string) {
  if (!orderId) return;

  try {
    if (action === "pay") {
      openPayConfirm(orderId);
      return;
    } else if (action === "ship") {
      await shipOrder(orderId);
    } else if (action === "confirm") {
      await confirmReceipt(orderId);
    } else if (action === "refund") {
      await refundOrder(orderId);
    }

    // refresh current tab list
    await loadOrders();

    // refresh detail if open
    if (detailOpen.value && detailOrder.value?.id === orderId) {
      try {
        const d = await getOrderDetail(orderId);
        detailOrder.value = normalizeOrder(d as any);
      } catch {
        // ignore
      }
    }
  } catch (e: any) {
    alert(e?.message || "操作失败");
  }
}
</script>