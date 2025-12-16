<template>
  <div
    v-if="open"
    id="order-detail-modal"
    class="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-6"
    @click.self="$emit('close')"
  >
    <div class="bg-white w-full max-w-5xl rounded-2xl shadow-modal overflow-hidden mx-4">
      <div class="p-6">
        <div class="flex justify-between items-start mb-6">
          <h2 id="modal-title" class="text-xl font-bold text-neutral-700">订单详情</h2>
          <button
            id="close-modal"
            class="text-neutral-400 hover:text-neutral-700 transition-colors"
            type="button"
            @click="$emit('close')"
          >
            <i class="fas fa-times text-xl"></i>
          </button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- 商品图片预览 -->
          <div id="modal-product-images" class="grid grid-cols-2 gap-3">
            <div
              v-for="(img, idx) in productImages"
              :key="idx"
              class="rounded-lg overflow-hidden border border-neutral-200 aspect-square"
            >
              <img :src="img" :alt="productTitle" class="w-full h-full object-cover" />
            </div>
          </div>

          <!-- 商品信息与订单信息 -->
          <div class="space-y-6">
            <div>
              <h3 class="text-lg font-semibold text-neutral-700 mb-2">商品信息</h3>
              <div class="space-y-3">
                <div>
                  <h4 id="modal-product-title" class="text-lg font-medium text-neutral-700">
                    {{ productTitle }}
                  </h4>
                  <p id="modal-product-specs" class="text-neutral-400 mt-1">
                    {{ productSpecs }}
                  </p>
                </div>
              </div>
            </div>

            <div>
              <h3 class="text-lg font-semibold text-neutral-700 mb-2">订单信息</h3>
              <div class="space-y-3 text-sm">
                <div>
                  <p class="text-neutral-400">订单编号</p>
                  <p id="modal-order-number" class="font-medium text-neutral-700">{{ order?.order_no || order?.id || "" }}</p>
                </div>

                <div>
                  <p class="text-neutral-400">卖家</p>
                  <p id="modal-seller" class="font-medium text-neutral-700">{{ sellerNameDisplay }}</p>
                </div>

                <div>
                  <p class="text-neutral-400">卖家地址</p>
                  <p id="modal-seller-address" class="font-medium text-neutral-700">{{ sellerAddressDisplay }}</p>
                </div>

                <div>
                  <p class="text-neutral-400">订单状态</p>
                  <p id="modal-order-status" class="font-medium" :class="textColorClass">
                    {{ order?.statusView || statusText }}
                  </p>
                </div>

                <div>
                  <p class="text-neutral-400">价格</p>
                  <p id="modal-order-amount" class="font-medium text-danger">¥{{ formatPrice(displayPrice) }}</p>
                </div>

                <div>
                  <p class="text-neutral-400">购买时间</p>
                  <p id="modal-purchase-time" class="font-medium text-neutral-700">{{ purchaseTimeText }}</p>
                </div>


              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="border-t border-neutral-200 p-6 flex justify-between items-center gap-3">
        <!-- Left side primary controls -->
        <div class="flex items-center gap-3">
          <template v-if="order?.status === 'pending_payment'">
            <button
              id="modal-pay-now"
              type="button"
              class="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary/90"
              @click="$emit('action', 'pay')"
            >
              立即付款
            </button>
            <button
              id="modal-cancel-order"
              type="button"
              class="px-4 py-2 rounded-lg border border-danger text-danger hover:bg-danger/5"
              @click="$emit('action', 'cancel_payment')"
            >
              取消订单
            </button>
          </template>

          <button
            v-else
            id="modal-close-btn"
            type="button"
            class="px-4 py-2 rounded-lg border border-neutral-300 text-neutral-700 hover:bg-neutral-50"
            @click="$emit('close')"
          >
            关闭
          </button>
        </div>

        <!-- Right side action buttons (same as operation column) -->
        <div id="modal-actions" class="flex gap-3">
          <button
            v-for="btn in actions"
            :key="btn.action"
            type="button"
            class="px-4 py-2 rounded-lg border border-neutral-300 text-neutral-700 hover:bg-neutral-50"
            :class="btn.className"
            @click="$emit('action', btn.action)"
          >
            {{ btn.text }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const formatPrice = (v: any) => {
  if (v === null || v === undefined || v === "") return "";
  const n = typeof v === "number" ? v : Number(v);
  if (Number.isFinite(n)) return n.toLocaleString();
  return String(v);
};

const API_ORIGIN = (import.meta as any).env?.VITE_API_ORIGIN || "http://127.0.0.1:8000";
const toAbsUrl = (u: string) => {
  if (!u) return "";
  if (u.startsWith("http://") || u.startsWith("https://")) return u;
  if (u.startsWith("/")) return `${API_ORIGIN}${u}`;
  return `${API_ORIGIN}/${u}`;
};

type Status =
  | "pending_payment"
  | "pending_shipment"
  | "pending_receipt"
  | "shipped"
  | "completed"
  | "refunded"
  | "received";

type OrderItem = {
  id: number | string;
  order_no?: string;
  status: Status;
  statusView?: string;

  buyer_id?: number;
  buyer_address?: string;
  seller_id?: number;
  seller_address?: string;
  seller_username?: string;

  product_id?: number;
  product_title?: string;
  product_main_image?: string;
  product_selling_price?: string;

  purchased_at?: string;
  created_at?: string;
  shipping_code?: string;

  // backward compat for other pages
  purchasePrice?: number;
  purchaseTime?: string;
  logisticsNumber?: string;
  price?: number;

  product?: { title: string; specs: string; images: string[]; thumbnail: string };
  buyerName?: string;
  sellerName?: string;
  buyer?: string;
  seller?: string;
};

const props = defineProps<{
  open: boolean;
  order: OrderItem | null;
  actions: { text: string; className: string; action: string }[];
  statusText: string;
  statusClass: string;
}>();

defineEmits<{
  (e: "close"): void;
  (e: "action", action: string): void;
}>();

// a.html 里在 JS 用了“只取文本颜色类”的做法，这里用一个更稳的：从 statusClass 里拆出 text-xxx
const textColorClass = computed(() => {
  const parts = (props.statusClass || "").split(" ").filter((c) => c.startsWith("text-"));
  return parts.join(" ");
});

const productTitle = computed(() => props.order?.product?.title || props.order?.product_title || "");
const productSpecs = computed(() => props.order?.product?.specs || "");
const productImages = computed(() => {
  const imgs = props.order?.product?.images || [];
  if (imgs.length) return imgs;
  const main = props.order?.product_main_image ? toAbsUrl(props.order.product_main_image) : "";
  return main ? [main] : [];
});

const displayPrice = computed(() => {
  const p = props.order?.product_selling_price;
  if (p !== undefined && p !== null && p !== "") return Number(p);
  return props.order?.purchasePrice ?? props.order?.price ?? 0;
});

const purchaseTimeText = computed(() => {
  return props.order?.purchased_at || props.order?.purchaseTime || props.order?.created_at || "";
});

const sellerNameDisplay = computed(() => {
  // Prefer upcoming API field `seller_name` (nick_name), then other known fields
  const o: any = props.order as any;
  return (
    o?.seller_name ||
    o?.seller_username ||
    o?.sellerName ||
    o?.seller ||
    (o?.seller_id !== undefined && o?.seller_id !== null ? `用户#${o.seller_id}` : "")
  );
});

const sellerAddressDisplay = computed(() => {
  const o: any = props.order as any;
  return o?.seller_address || o?.sellerAddress || "暂无";
});
</script>