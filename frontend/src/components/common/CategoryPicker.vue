<script setup lang="ts">
import { computed, ref, watch } from "vue";

type Category = {
  id: number | string;
  name: string;
  code?: string;
};

const props = withDefaults(
  defineProps<{
    categories: Category[];
    title?: string;
    subtitle?: string;
    enterText?: string;
    defaultSelectedIndex?: number;
  }>(),
  {
    title: "选择商品分类",
    subtitle: "请选择一个分类后点击进入",
    enterText: "点击进入",
    defaultSelectedIndex: 0,
  }
);

const emit = defineEmits<{
  (e: "select", categoryId: number | string): void;
  (e: "enter", categoryId: number | string): void;
}>();

const selectedIndex = ref<number>(Math.max(0, props.defaultSelectedIndex));

watch(
  () => props.categories,
  (list) => {
    if (!Array.isArray(list) || list.length === 0) {
      selectedIndex.value = 0;
      return;
    }
    if (selectedIndex.value < 0 || selectedIndex.value >= list.length) {
      selectedIndex.value = 0;
    }
  },
  { immediate: true }
);

const selectedCategory = computed(() => props.categories?.[selectedIndex.value] || null);

function selectCard(index: number) {
  selectedIndex.value = index;
  const c = props.categories?.[index];
  if (c) emit("select", c.id);
}

function onEnter() {
  if (!selectedCategory.value) return;
  emit("enter", selectedCategory.value.id);
}

function normCode(code?: string) {
  return (code || "").toLowerCase();
}

function emojiFor(c: Category) {
  const code = normCode(c.code);
  const name = (c.name || "").toLowerCase();

  if (code.includes("mobile") || code.includes("phone") || name.includes("手机")) return "📱";
  if (code.includes("laptop") || code.includes("notebook") || name.includes("笔记本") || name.includes("电脑")) return "💻";
  if (code.includes("tablet") || code.includes("pad") || name.includes("平板")) return "📟";
  if (code.includes("camera") || name.includes("相机")) return "📷";
  if (code.includes("watch") || name.includes("手表") || name.includes("手环")) return "⌚";
  if (code.includes("audio") || code.includes("headphone") || name.includes("耳机") || name.includes("音箱")) return "🎧";
  if (code.includes("console") || name.includes("游戏") || name.includes("主机")) return "🎮";
  if (code.includes("accessory") || name.includes("配件")) return "🔌";
  return "🏷️";
}

function iconClass(c: Category) {
  const code = normCode(c.code);
  const name = (c.name || "").toLowerCase();

  if (code.includes("mobile") || code.includes("phone") || name.includes("手机")) return "fas fa-mobile-alt";
  if (code.includes("laptop") || code.includes("notebook") || name.includes("笔记本") || name.includes("电脑")) return "fas fa-laptop";
  if (code.includes("tablet") || code.includes("pad") || name.includes("平板")) return "fas fa-tablet-alt";
  if (code.includes("camera") || name.includes("相机")) return "fas fa-camera";
  if (code.includes("watch") || name.includes("手表") || name.includes("手环")) return "fas fa-clock";
  if (code.includes("audio") || code.includes("headphone") || name.includes("耳机") || name.includes("音箱")) return "fas fa-headphones";
  if (code.includes("console") || name.includes("游戏") || name.includes("主机")) return "fas fa-gamepad";
  if (code.includes("accessory") || name.includes("配件")) return "fas fa-plug";
  return "fas fa-tag";
}
</script>

<template>
  <div
    class="min-h-[calc(100vh-64px)] p-4 font-sans select-none flex flex-col items-center bg-transparent"
  >
    <!-- 标题 -->
    <div class="w-full max-w-[1400px] mt-4">
      <h1 class="text-3xl md:text-5xl font-extrabold text-purple-600 drop-shadow-sm text-center">
        {{ title }}
      </h1>
      <p v-if="subtitle" class="text-center text-slate-600 mt-2 text-sm md:text-base">
        {{ subtitle }}
      </p>
    </div>

    <!-- 卡片网格容器 -->
    <div
      class="w-full max-w-[1400px] grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4 md:gap-6 mb-10 mt-8"
    >
      <div
        v-for="(c, index) in categories"
        :key="c.id"
        @click="selectCard(index)"
        class="relative group cursor-pointer transition-all duration-300 ease-out"
        :class="[selectedIndex === index ? 'z-10 scale-105' : 'hover:scale-102 hover:-translate-y-1']"
      >
        <!-- 选中时的光标 (左侧箭头) -->
        <div
          v-if="selectedIndex === index"
          class="absolute -left-3 top-1/2 -translate-y-1/2 w-0 h-0 border-t-[10px] border-t-transparent border-r-[12px] border-r-gray-600 border-b-[10px] border-b-transparent z-20 drop-shadow-md hidden md:block animate-pulse"
        ></div>

        <!-- 卡片主体 -->
        <div
          class="bg-white/80 backdrop-blur-md rounded-[2rem] p-3 shadow-lg border-2 transition-all duration-300 flex flex-col items-center justify-between h-[220px]"
          :class="[
            selectedIndex === index
              ? 'border-yellow-300 ring-4 ring-yellow-100 shadow-yellow-200/50'
              : 'border-white/50 hover:border-white hover:shadow-xl'
          ]"
        >
          <!-- 顶部信息: code & icon -->
          <div class="w-full flex justify-between items-center text-sm font-bold px-2">
            <span class="text-cyan-600 truncate max-w-[70%]">{{ c.code || 'category' }}</span>
            <span class="text-purple-600 text-lg"><i :class="iconClass(c)"></i></span>
          </div>

          <!-- 图标区域 -->
          <div class="relative w-24 h-24 flex items-center justify-center">
            <!-- 背景淡色圆圈 -->
            <div class="absolute inset-0 bg-gradient-to-b from-gray-100 to-gray-200 rounded-full opacity-50 scale-90"></div>
            <!-- Emoji 图标 -->
            <div class="relative z-10 w-full h-full flex items-center justify-center text-5xl">
              {{ emojiFor(c) }}
            </div>
            <!-- 选中时小标记 -->
            <div v-if="selectedIndex === index" class="absolute bottom-2 right-2 text-pink-500 animate-bounce">
              ★
            </div>
          </div>

          <!-- 分类名 -->
          <div class="text-gray-800 font-extrabold text-lg -mt-2 truncate w-full text-center">
            {{ c.name }}
          </div>

          <!-- 装饰条（替代 HP） -->
          <div class="w-full px-2 mb-1">
            <div class="w-full h-3 bg-gray-200 rounded-full overflow-hidden border border-gray-300/50">
              <div
                class="h-full rounded-full transition-all duration-300 ease-out"
                :class="selectedIndex === index ? 'bg-yellow-400' : 'bg-emerald-400'"
                :style="{ width: selectedIndex === index ? '100%' : '72%' }"
              ></div>
            </div>
            <div class="text-[10px] text-gray-400 text-center font-bold mt-1">
              {{ selectedIndex === index ? '已选择' : '点击选择' }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部操作区 -->
    <div class="flex flex-col items-center gap-4 pb-10">
      <button
        @click="onEnter"
        class="bg-white border-2 border-orange-200 text-gray-700 font-extrabold py-3 px-10 rounded-full shadow-md hover:bg-orange-50 hover:scale-105 active:scale-95 transition-all disabled:opacity-60 disabled:cursor-not-allowed"
        :disabled="!selectedCategory"
      >
        {{ enterText }}
      </button>

      <div v-if="selectedCategory" class="text-xs text-slate-500 text-center">
        当前选择：<span class="font-bold text-slate-700">{{ selectedCategory.name }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 保留像素风格类名（可复用） */
.rendering-pixelated {
  image-rendering: pixelated;
}
</style>