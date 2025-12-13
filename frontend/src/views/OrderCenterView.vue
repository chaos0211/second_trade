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
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import OrderTable from "@/components/orders/OrderTable.vue";
import OrderDetailModal from "@/components/orders/OrderDetailModal.vue";

type Status = "pending" | "paid" | "completed" | "canceled";
type Tab = "bought" | "sold";

type OrderItem = {
  id: string;
  product: {
    id: string;
    title: string;
    specs: string;
    images: string[];
    thumbnail: string;
  };
  time: string;
  price: number;
  status: Status;
  buyer: string;
  seller: string;
  logisticsNumber: string;
  createTime: string;
  paymentTime: string;
  completionTime: string;
};

const tab = ref<Tab>("bought");
const page = ref(1);
const pageSize = ref(10);
const loading = ref(true);

const detailOpen = ref(false);
const detailOrder = ref<OrderItem | null>(null);

// ====== 下面这份 mock 数据结构严格沿用 a.html（你后面换成真实接口时只要保持字段名即可）=====
const mockOrders = ref<Record<Tab, OrderItem[]>>({
  bought: [
    {
      id: "ORD20250115001",
      product: {
        id: "PROD1001",
        title: "Apple iPhone 14 Pro 256GB 星光色",
        specs: "品牌：Apple | 型号：iPhone 14 Pro | 容量：256GB | 颜色：星光色 | 成色：99新",
        images: [
          "https://design.gemcoder.com/staticResource/echoAiSystemImages/98628ca8f8f03decbb85fc075735f4a7.png",
          "https://design.gemcoder.com/staticResource/echoAiSystemImages/35bed43088426e24ed2e0c8460b97a84.png",
          "https://design.gemcoder.com/staticResource/echoAiSystemImages/272058d13a3dda6c167ff9dcbaf2fa20.png",
          "https://design.gemcoder.com/staticResource/echoAiSystemImages/b2291d128062d132c0c1c60f5662571a.png",
        ],
        thumbnail:
          "https://design.gemcoder.com/staticResource/echoAiSystemImages/28ba681c048e09cf3bd9059065e07f5a.png",
      },
      time: "2025-01-15 14:20",
      price: 7999,
      status: "paid",
      buyer: "张小明",
      seller: "科技数码专营店",
      logisticsNumber: "SF1234567890123",
      createTime: "2025-01-15 14:15",
      paymentTime: "2025年01月15日 14:20",
      completionTime: "",
    },
  ],
  sold: [
    {
      id: "ORD20250114001",
      product: {
        id: "PROD2001",
        title: "微软 Surface Pro 9 i5 8GB+256GB",
        specs: "品牌：微软 | 型号：Surface Pro 9 | 配置：i5/8GB/256GB | 成色：95新",
        images: [
          "https://design.gemcoder.com/staticResource/echoAiSystemImages/32c66da6e722d6140d060f052e8b3caa.png",
          "https://design.gemcoder.com/staticResource/echoAiSystemImages/8421fc4ede212c013d2b8eda2ee2e259.png",
        ],
        thumbnail:
          "https://design.gemcoder.com/staticResource/echoAiSystemImages/efeef04452439f8cabd68a0872c3a32d.png",
      },
      time: "2025-01-14 10:30",
      price: 5999,
      status: "paid",
      buyer: "李华",
      seller: "张小明",
      logisticsNumber: "SF1234567890456",
      createTime: "2025-01-14 10:20",
      paymentTime: "2025年01月14日 10:30",
      completionTime: "",
    },
  ],
});

function loadOrders() {
  loading.value = true;
  setTimeout(() => {
    loading.value = false;
  }, 500);
}

onMounted(loadOrders);

const currentOrdersAll = computed(() => mockOrders.value[tab.value] || []);
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

function openOrderDetail(orderId: string) {
  const found = currentOrdersAll.value.find((o) => o.id === orderId) || null;
  if (!found) return;
  detailOrder.value = found;
  detailOpen.value = true;
  document.body.style.overflow = "hidden";
}

function closeModal() {
  detailOpen.value = false;
  detailOrder.value = null;
  document.body.style.overflow = "";
}

// ====== 状态工具：保持与 a.html 一致 ======
function getStatusClass(status?: Status) {
  switch (status) {
    case "pending":
      return "bg-warning/10 text-warning";
    case "paid":
      return "bg-primary/10 text-primary";
    case "completed":
      return "bg-success/10 text-success";
    case "canceled":
      return "bg-danger/10 text-danger";
    default:
      return "bg-neutral-100 text-neutral-500";
  }
}

function getStatusText(status?: Status) {
  switch (status) {
    case "pending":
      return "待付款";
    case "paid":
      return "已付款";
    case "completed":
      return "已完成";
    case "canceled":
      return "已取消";
    default:
      return "未知状态";
  }
}

function getActionButtons(status?: Status) {
  const buttons: { text: string; className: string; action: string }[] = [];
  switch (status) {
    case "pending":
      buttons.push({ text: "去支付", className: "btn-primary", action: "pay" });
      buttons.push({ text: "取消订单", className: "btn-danger", action: "cancel" });
      break;
    case "paid":
      buttons.push({ text: "确认收货", className: "btn-primary", action: "confirm" });
      buttons.push({ text: "申请退款", className: "btn-secondary", action: "refund" });
      break;
    case "completed":
      buttons.push({ text: "查看详情", className: "btn-secondary", action: "detail" });
      buttons.push({ text: "再次购买", className: "btn-primary", action: "repurchase" });
      break;
    case "canceled":
      buttons.push({ text: "删除记录", className: "btn-secondary", action: "delete" });
      buttons.push({ text: "再次购买", className: "btn-primary", action: "repurchase" });
      break;
  }
  return buttons;
}

// ====== 订单操作：先保持 a.html 的行为（alert/confirm），后面你再接真实接口 ======
function handleOrderAction(orderId: string | undefined, action: string) {
  if (!orderId) return;
  const list = mockOrders.value[tab.value];
  const order = list.find((o) => o.id === orderId);
  if (!order) return;

  switch (action) {
    case "pay":
      alert(`去支付订单:${order.id}`);
      break;
    case "cancel":
      if (confirm(`确定要取消订单${order.id}吗？`)) order.status = "canceled";
      break;
    case "confirm":
      if (confirm(`确定要确认收货订单${order.id}吗？`)) {
        order.status = "completed";
        order.completionTime = new Date().toLocaleString("zh-CN", {
          year: "numeric",
          month: "long",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        });
      }
      break;
    case "refund":
      alert(`申请退款订单:${order.id}`);
      break;
    case "detail":
      openOrderDetail(order.id);
      break;
    case "repurchase":
      alert(`再次购买商品:${order.product.title}`);
      break;
    case "delete":
      if (confirm(`确定要删除订单记录${order.id}吗？`)) {
        mockOrders.value[tab.value] = list.filter((o) => o.id !== order.id);
        closeModal();
      }
      break;
  }
}
</script>