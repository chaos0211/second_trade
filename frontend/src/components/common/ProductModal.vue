<template>
  <div
    class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center transition-all duration-300"
    :class="open ? 'opacity-100 visible' : 'opacity-0 invisible'"
    @click.self="open = false"
  >
    <div class="bg-white rounded-xl shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col transform transition-all duration-300"
         :class="open ? 'scale-100' : 'scale-95'">
      <div class="p-6 border-b border-light-2 flex items-center justify-between">
        <h3 class="text-xl font-bold text-dark">商品详情</h3>
        <button class="text-dark-2 hover:text-dark transition-colors" @click="open = false">
          <i class="fas fa-times text-xl"></i>
        </button>
      </div>

      <div class="flex-1 overflow-y-auto p-6">
        <!-- 这里可以继续把你 HTML 的详情内容原样搬进来，
             只要把主图/缩略图用 activeImgIndex 控制即可 -->
        <div class="text-dark-2">
          <div class="font-medium text-dark mb-2">{{ product?.title ?? '未选择商品' }}</div>
          <div class="text-sm">（这里放完整详情区块，保持你的原样式）</div>
        </div>
      </div>

      <div class="p-6 border-t border-light-2 bg-light-3/50">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <button class="px-4 py-2 border border-danger text-danger rounded-lg hover:bg-danger/5 transition-colors">
              <i class="fas fa-heart mr-2"></i>加入收藏
            </button>
            <button class="px-4 py-2 border border-primary text-primary rounded-lg hover:bg-primary/5 transition-colors">
              <i class="fas fa-shopping-cart mr-2"></i>加入购物车
            </button>
          </div>
          <button class="px-8 py-3 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors shadow-sm hover:shadow">
            立即购买
          </button>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
const open = defineModel<boolean>("open", { required: true });
defineProps<{ product: any | null }>();
</script>