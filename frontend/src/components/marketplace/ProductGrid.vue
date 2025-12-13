<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
    <ProductCard
      v-for="p in items"
      :key="p.id"
      :item="p"
      @open="$emit('open', p)"
    />
  </div>
</template>

<script setup lang="ts">
import ProductCard from "./ProductCard.vue";
defineProps<{ items: any[] }>();
defineEmits<{ (e: "open", p: any): void }>();
</script>