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
              v-for="(img, idx) in (order?.product.images || [])"
              :key="idx"
              class="rounded-lg overflow-hidden border border-neutral-200 aspect-square"
            >
              <img :src="img" :alt="order?.product.title" class="w-full h-full object-cover" />
            </div>
          </div>

          <!-- 商品信息与订单信息 -->
          <div class="space-y-6">
            <div>
              <h3 class="text-lg font-semibold text-neutral-700 mb-2">商品信息</h3>
              <div class="space-y-3">
                <div>
                  <h4 id="modal-product-title" class="text-lg font-medium text-neutral-700">
                    {{ order?.product.title || "" }}
                  </h4>
                  <p id="modal-product-specs" class="text-neutral-400 mt-1">
                    {{ order?.product.specs || "" }}
                  </p>
                </div>
              </div>
            </div>

            <div>
              <h3 class="text-lg font-semibold text-neutral-700 mb-2">订单信息</h3>
              <div class="grid grid-cols-2 gap-y-3 gap-x-4 text-sm">
                <div>
                  <p class="text-neutral-400">订单编号</p>
                  <p id="modal-order-number" class="font-medium text-neutral-700">{{ order?.id || "" }}</p>
                </div>
                <div>
                  <p class="text-neutral-400">买家</p>
                  <p id="modal-buyer" class="font-medium text-neutral-700">{{ order?.buyer || "" }}</p>
                </div>
                <div>
                  <p class="text-neutral-400">卖家</p>
                  <p id="modal-seller" class="font-medium text-neutral-700">{{ order?.seller || "" }}</p>
                </div>
                <div>
                  <p class="text-neutral-400">订单状态</p>
                  <p id="modal-order-status" class="font-medium" :class="textColorClass">
                    {{ statusText }}
                  </p>
                </div>
                <div>
                  <p class="text-neutral-400">成交金额</p>
                  <p id="modal-order-amount" class="font-medium text-danger">
                    ¥{{ order?.price?.toLocaleString?.() || "" }}
                  </p>
                </div>
                <div>
                  <p class="text-neutral-400">物流单号</p>
                  <p id="modal-logistics-number" class="font-medium text-neutral-700">
                    {{ order?.logisticsNumber || "暂无" }}
                  </p>
                </div>
              </div>
            </div>

            <div>
              <h3 class="text-lg font-semibold text-neutral-700 mb-2">时间信息</h3>
              <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-neutral-400">创建时间</span>
                  <span id="modal-create-time" class="text-neutral-700">{{ order?.createTime || "" }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-neutral-400">付款时间</span>
                  <span id="modal-payment-time" class="text-neutral-700">{{ order?.paymentTime || "未付款" }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-neutral-400">完成时间</span>
                  <span id="modal-completion-time" class="text-neutral-700">{{ order?.completionTime || "未完成" }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="border-t border-neutral-200 p-6 flex justify-end gap-3">
        <button id="modal-close-btn" class="btn btn-secondary" type="button" @click="$emit('close')">关闭</button>
        <div id="modal-actions" class="flex gap-3">
          <button
            v-for="btn in actions"
            :key="btn.action"
            class="btn"
            :class="btn.className"
            type="button"
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

type Status = "pending" | "paid" | "completed" | "canceled";

type OrderItem = {
  id: string;
  product: { title: string; specs: string; images: string[]; thumbnail: string };
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
</script>