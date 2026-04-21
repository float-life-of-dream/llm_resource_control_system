<template>
  <div class="stat-card">
    <span class="label">{{ item.label }}</span>
    <strong>{{ item.value }}</strong>
    <span class="unit">{{ item.unit }}</span>
  </div>
</template>

<script setup lang="ts">
import type { OverviewItem } from "../types/monitor";

defineProps<{
  item: OverviewItem;
}>();
</script>

<style scoped>
.stat-card {
  background: linear-gradient(160deg, rgba(29, 44, 69, 0.94), rgba(13, 20, 33, 0.98));
  border: 1px solid rgba(143, 163, 191, 0.18);
  border-radius: 20px;
  padding: 20px;
  min-height: 132px;
  display: grid;
  gap: 10px;
}

.label,
.unit {
  color: #8fa3bf;
}

strong {
  font-size: 40px;
  line-height: 1;
}
</style>
