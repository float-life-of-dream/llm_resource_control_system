<template>
  <AdminLayout>
    <section class="page-grid">
      <PageHeader :generated-at="new Date().toISOString()" />
      <el-table :data="sessions">
        <el-table-column prop="userAgent" label="User Agent" />
        <el-table-column prop="ipAddress" label="IP" />
        <el-table-column prop="expiresAt" label="Expires" />
        <el-table-column prop="lastUsedAt" label="Last Used" />
        <el-table-column label="Actions" width="140">
          <template #default="{ row }">
            <el-button link type="danger" @click="revoke(row.id)">Revoke</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </AdminLayout>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";

import { fetchSessions, revokeSession } from "../api/auth";
import PageHeader from "../components/PageHeader.vue";
import AdminLayout from "../layouts/AdminLayout.vue";
import type { SessionItem } from "../types/auth";

const sessions = ref<SessionItem[]>([]);

async function load() {
  sessions.value = (await fetchSessions()).items;
}

async function revoke(sessionId: string) {
  await revokeSession(sessionId);
  await load();
}

onMounted(() => {
  void load();
});
</script>

<style scoped>
.page-grid {
  display: grid;
  gap: 24px;
}
</style>
