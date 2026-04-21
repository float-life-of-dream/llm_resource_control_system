<template>
  <div class="page-header">
    <div>
      <p class="eyebrow">AI Resource Monitor</p>
      <h1>Dashboard</h1>
    </div>
    <div class="meta">
      <span>Prometheus driven</span>
      <span v-if="generatedAt">Updated {{ formattedTime }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  generatedAt: string;
}>();

const formattedTime = computed(() => {
  if (!props.generatedAt) {
    return "";
  }

  return new Date(props.generatedAt).toLocaleString("zh-CN");
});
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 16px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #8fa3bf;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-size: 12px;
}

h1 {
  margin: 0;
  font-size: clamp(32px, 6vw, 48px);
}

.meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: #8fa3bf;
  text-align: right;
}
</style>
