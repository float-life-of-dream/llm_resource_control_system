<template>
  <AdminLayout>
    <section class="page-grid">
      <PageHeader :generated-at="new Date().toISOString()" />
      <div class="toolbar">
        <h2>Tenant Members</h2>
        <el-button v-if="canManage" type="primary" @click="openCreateDialog">New Member</el-button>
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
        <el-form ref="memberFormRef" :model="form" :rules="memberRules" label-position="top">
          <el-form-item label="Full Name" prop="fullName"><el-input v-model="form.fullName" /></el-form-item>
          <el-form-item label="Email" prop="email"><el-input v-model="form.email" /></el-form-item>
          <el-form-item label="Password" prop="password">
            <el-input v-model="form.password" show-password />
            <div class="field-hint">Password must be at least 8 characters.</div>
          </el-form-item>
          <el-form-item label="Role" prop="role">
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
import { ElMessage } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";

import { createTenantMember, deleteTenantMember, fetchTenantMembers, updateTenantMember } from "../api/tenant";
import AdminLayout from "../layouts/AdminLayout.vue";
import PageHeader from "../components/PageHeader.vue";
import { useAuthStore } from "../stores/auth";
import type { Membership, TenantRole } from "../types/auth";

const authStore = useAuthStore();
const members = ref<Membership[]>([]);
const dialogVisible = ref(false);
const memberFormRef = ref<FormInstance>();
const form = reactive({
  fullName: "",
  email: "",
  password: "",
  role: "viewer" as TenantRole,
});
const canManage = computed(() => ["owner", "admin"].includes(authStore.membershipRole ?? ""));
const memberRules: FormRules = {
  fullName: [{ required: true, message: "Full name is required.", trigger: "blur" }],
  email: [
    { required: true, message: "Email is required.", trigger: "blur" },
    { type: "email", message: "Please enter a valid email address.", trigger: ["blur", "change"] },
  ],
  password: [
    { required: true, message: "Password is required.", trigger: "blur" },
    { min: 8, message: "Password must be at least 8 characters.", trigger: ["blur", "change"] },
  ],
  role: [{ required: true, message: "Role is required.", trigger: "change" }],
};

async function loadMembers() {
  members.value = (await fetchTenantMembers()).items;
}

function openCreateDialog() {
  memberFormRef.value?.clearValidate();
  dialogVisible.value = true;
}

async function createMember() {
  const isValid = await memberFormRef.value?.validate().catch(() => false);
  if (!isValid) {
    return;
  }

  try {
    await createTenantMember(form);
    dialogVisible.value = false;
    form.fullName = "";
    form.email = "";
    form.password = "";
    form.role = "viewer";
    await loadMembers();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "Failed to create member.");
  }
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

.field-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #8fa3bf;
}
</style>
