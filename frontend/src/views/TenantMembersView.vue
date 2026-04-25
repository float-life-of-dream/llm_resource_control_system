<template>
  <AdminLayout>
    <section class="page-grid">
      <PageHeader :generated-at="new Date().toISOString()" />
      <div class="toolbar">
        <h2>Tenant Members</h2>
        <el-button v-if="canManage" type="primary" @click="dialogVisible = true">New Member</el-button>
      </div>
      <el-table :data="members">
        <el-table-column prop="user.fullName" label="Name" />
        <el-table-column prop="user.email" label="Email" />
        <el-table-column prop="role" label="Role" />
        <el-table-column label="Actions" width="240">
          <template #default="{ row }">
            <el-select v-if="canManage" :model-value="row.role" @change="(value: string | number | boolean) => updateRole(row.id, value)">
              <el-option label="Owner" value="owner" />
              <el-option label="Admin" value="admin" />
              <el-option label="Viewer" value="viewer" />
            </el-select>
            <el-button v-if="canManage" link type="danger" @click="removeMember(row.id)">Delete</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-dialog v-model="dialogVisible" title="Create Member">
        <el-form :model="form" label-position="top">
          <el-form-item label="Full Name"><el-input v-model="form.fullName" /></el-form-item>
          <el-form-item label="Email"><el-input v-model="form.email" /></el-form-item>
          <el-form-item label="Password"><el-input v-model="form.password" show-password /></el-form-item>
          <el-form-item label="Role">
            <el-select v-model="form.role">
              <el-option label="Owner" value="owner" />
              <el-option label="Admin" value="admin" />
              <el-option label="Viewer" value="viewer" />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="dialogVisible = false">Cancel</el-button>
          <el-button type="primary" @click="createMember">Create</el-button>
        </template>
      </el-dialog>
    </section>
  </AdminLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { createTenantMember, deleteTenantMember, fetchTenantMembers, updateTenantMember } from "../api/tenant";
import AdminLayout from "../layouts/AdminLayout.vue";
import PageHeader from "../components/PageHeader.vue";
import { useAuthStore } from "../stores/auth";
import type { Membership, TenantRole } from "../types/auth";

const authStore = useAuthStore();
const members = ref<Membership[]>([]);
const dialogVisible = ref(false);
const form = reactive({
  fullName: "",
  email: "",
  password: "",
  role: "viewer" as TenantRole,
});
const canManage = computed(() => ["owner", "admin"].includes(authStore.membershipRole ?? ""));

async function loadMembers() {
  members.value = (await fetchTenantMembers()).items;
}

async function createMember() {
  await createTenantMember(form);
  dialogVisible.value = false;
  form.fullName = "";
  form.email = "";
  form.password = "";
  form.role = "viewer";
  await loadMembers();
}

async function updateRole(membershipId: string, value: string | number | boolean) {
  await updateTenantMember(membershipId, value as TenantRole);
  await loadMembers();
}

async function removeMember(membershipId: string) {
  await deleteTenantMember(membershipId);
  await loadMembers();
}

onMounted(() => {
  void loadMembers();
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
