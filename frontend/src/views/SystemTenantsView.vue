<template>
  <AdminLayout>
    <section class="page-grid">
      <PageHeader :generated-at="new Date().toISOString()" />
      <div class="toolbar">
        <h2>System Tenants</h2>
        <el-button type="primary" @click="tenantDialog = true">New Tenant</el-button>
      </div>
      <el-table :data="tenants">
        <el-table-column prop="name" label="Name" />
        <el-table-column prop="slug" label="Slug" />
        <el-table-column label="Actions" width="180">
          <template #default="{ row }">
            <el-button link type="primary" @click="openMemberDialog(row.id)">Add Member</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-dialog v-model="tenantDialog" title="Create Tenant">
        <el-form :model="tenantForm" label-position="top">
          <el-form-item label="Name"><el-input v-model="tenantForm.name" /></el-form-item>
          <el-form-item label="Slug"><el-input v-model="tenantForm.slug" /></el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="tenantDialog = false">Cancel</el-button>
          <el-button type="primary" @click="createTenantAction">Create</el-button>
        </template>
      </el-dialog>

      <el-dialog v-model="memberDialog" title="Create Tenant Member">
        <el-form :model="memberForm" label-position="top">
          <el-form-item label="Full Name"><el-input v-model="memberForm.fullName" /></el-form-item>
          <el-form-item label="Email"><el-input v-model="memberForm.email" /></el-form-item>
          <el-form-item label="Password"><el-input v-model="memberForm.password" show-password /></el-form-item>
          <el-form-item label="Role">
            <el-select v-model="memberForm.role">
              <el-option label="Owner" value="owner" />
              <el-option label="Admin" value="admin" />
              <el-option label="Viewer" value="viewer" />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="memberDialog = false">Cancel</el-button>
          <el-button type="primary" @click="createTenantMemberAction">Create</el-button>
        </template>
      </el-dialog>
    </section>
  </AdminLayout>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";

import { createSystemTenant, createSystemTenantMember, fetchSystemTenants } from "../api/system";
import PageHeader from "../components/PageHeader.vue";
import AdminLayout from "../layouts/AdminLayout.vue";
import type { TenantProfile, TenantRole } from "../types/auth";

const tenants = ref<TenantProfile[]>([]);
const tenantDialog = ref(false);
const memberDialog = ref(false);
const selectedTenantId = ref("");
const tenantForm = reactive({ name: "", slug: "" });
const memberForm = reactive({
  fullName: "",
  email: "",
  password: "",
  role: "owner" as TenantRole,
});

async function load() {
  tenants.value = (await fetchSystemTenants()).items;
}

function openMemberDialog(tenantId: string) {
  selectedTenantId.value = tenantId;
  memberDialog.value = true;
}

async function createTenantAction() {
  await createSystemTenant(tenantForm);
  tenantDialog.value = false;
  tenantForm.name = "";
  tenantForm.slug = "";
  await load();
}

async function createTenantMemberAction() {
  await createSystemTenantMember(selectedTenantId.value, memberForm);
  memberDialog.value = false;
  memberForm.fullName = "";
  memberForm.email = "";
  memberForm.password = "";
  memberForm.role = "owner";
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

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
