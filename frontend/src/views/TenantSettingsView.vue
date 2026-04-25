<template>
  <AdminLayout>
    <section class="page-grid">
      <PageHeader :generated-at="new Date().toISOString()" />
      <div class="panel">
        <h2>Tenant Settings</h2>
        <el-form label-position="top">
          <el-form-item label="Tenant Name">
            <el-input v-model="name" />
          </el-form-item>
          <el-button type="primary" @click="save">Save</el-button>
        </el-form>
      </div>
    </section>
  </AdminLayout>
</template>

<script setup lang="ts">
import { ref } from "vue";

import { updateTenant } from "../api/tenant";
import PageHeader from "../components/PageHeader.vue";
import AdminLayout from "../layouts/AdminLayout.vue";
import { useAuthStore } from "../stores/auth";

const authStore = useAuthStore();
const name = ref(authStore.tenant?.name ?? "");

async function save() {
  const tenant = await updateTenant(name.value);
  authStore.tenant = tenant;
}
</script>

<style scoped>
.page-grid {
  display: grid;
  gap: 24px;
}

.panel {
  padding: 24px;
  border-radius: 24px;
  background: rgba(10, 17, 28, 0.96);
  border: 1px solid rgba(143, 163, 191, 0.2);
}
</style>
