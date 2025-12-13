<template>
  <div class="bg-white rounded-xl shadow-card p-4 mb-6">
    <div class="flex flex-wrap gap-4">
      <div class="w-full md:w-auto">
        <label class="block text-sm font-medium text-dark-2 mb-1">品牌</label>
        <div class="relative">
          <select v-model="m.brand" class="w-full md:w-40 appearance-none bg-light-3 border border-light-2 rounded-lg px-4 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary">
            <option value="">全部品牌</option>
            <option value="apple">Apple</option>
            <option value="samsung">Samsung</option>
            <option value="huawei">华为</option>
            <option value="xiaomi">小米</option>
            <option value="oppo">OPPO</option>
            <option value="vivo">vivo</option>
          </select>
          <i class="fas fa-chevron-down absolute right-3 top-1/2 transform -translate-y-1/2 text-light-1 pointer-events-none"></i>
        </div>
      </div>

      <div class="w-full md:w-auto">
        <label class="block text-sm font-medium text-dark-2 mb-1">成色</label>
        <div class="relative">
          <select v-model="m.condition" class="w-full md:w-40 appearance-none bg-light-3 border border-light-2 rounded-lg px-4 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary">
            <option value="">全部成色</option>
            <option value="new">全新未拆封</option>
            <option value="like-new">99新</option>
            <option value="excellent">95新</option>
            <option value="good">9成新</option>
            <option value="fair">8成新</option>
          </select>
          <i class="fas fa-chevron-down absolute right-3 top-1/2 transform -translate-y-1/2 text-light-1 pointer-events-none"></i>
        </div>
      </div>

      <div class="w-full md:w-auto">
        <label class="block text-sm font-medium text-dark-2 mb-1">价格区间</label>
        <div class="relative">
          <select v-model="m.priceRange" class="w-full md:w-48 appearance-none bg-light-3 border border-light-2 rounded-lg px-4 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary">
            <option value="">全部价格</option>
            <option value="0-1000">￥0 - ￥1000</option>
            <option value="1000-2000">￥1000 - ￥2000</option>
            <option value="2000-3000">￥2000 - ￥3000</option>
            <option value="3000-5000">￥3000 - ￥5000</option>
            <option value="5000+">￥5000以上</option>
          </select>
          <i class="fas fa-chevron-down absolute right-3 top-1/2 transform -translate-y-1/2 text-light-1 pointer-events-none"></i>
        </div>
      </div>

      <div class="w-full md:w-auto ml-auto md:ml-0">
        <label class="block text-sm font-medium text-dark-2 mb-1">排序方式</label>
        <div class="relative">
          <select v-model="m.sort" class="w-full md:w-40 appearance-none bg-light-3 border border-light-2 rounded-lg px-4 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary">
            <option value="recommend">推荐排序</option>
            <option value="price-asc">价格从低到高</option>
            <option value="price-desc">价格从高到低</option>
            <option value="newest">最新发布</option>
            <option value="hottest">最热销量</option>
          </select>
          <i class="fas fa-chevron-down absolute right-3 top-1/2 transform -translate-y-1/2 text-light-1 pointer-events-none"></i>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const m = defineModel<any>({ required: true });
</script>