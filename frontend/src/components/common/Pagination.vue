cat > frontend/src/components/common/Pagination.vue <<'EOF'
<template>
  <div class="flex items-center justify-between">
    <div class="text-sm text-dark-2">
      共 <span class="font-medium text-dark">{{ total }}</span> 条
    </div>

    <div class="flex items-center space-x-2">
      <button
        class="px-3 py-2 rounded-lg border border-light-2 bg-white text-dark-2 hover:bg-light-3 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        :disabled="current <= 1"
        @click="go(current - 1)"
      >
        <i class="fas fa-chevron-left"></i>
      </button>

      <button
        v-for="p in pages"
        :key="p"
        class="w-10 h-10 rounded-lg border transition-colors"
        :class="p === current ? 'bg-primary text-white border-primary' : 'bg-white text-dark-2 border-light-2 hover:bg-light-3'"
        @click="go(p)"
      >
        {{ p }}
      </button>

      <button
        class="px-3 py-2 rounded-lg border border-light-2 bg-white text-dark-2 hover:bg-light-3 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        :disabled="current >= pageCount"
        @click="go(current + 1)"
      >
        <i class="fas fa-chevron-right"></i>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  current?: number
  pageSize?: number
  total?: number
}>(), {
  current: 1,
  pageSize: 12,
  total: 0,
})

const emit = defineEmits<{
  (e: 'update:current', v: number): void
  (e: 'change', v: number): void
}>()

const pageCount = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))

const pages = computed(() => {
  const c = props.current
  const n = pageCount.value
  // 简单展示：最多 5 个页码
  const start = Math.max(1, c - 2)
  const end = Math.min(n, start + 4)
  const realStart = Math.max(1, end - 4)
  const arr: number[] = []
  for (let i = realStart; i <= end; i++) arr.push(i)
  return arr
})

function go(p: number) {
  const next = Math.min(pageCount.value, Math.max(1, p))
  emit('update:current', next)
  emit('change', next)
}
</script>
EOF