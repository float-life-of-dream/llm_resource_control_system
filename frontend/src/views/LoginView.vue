<template>
  <div class="login-shell">
    <div class="card">
      <p class="eyebrow">AI Monitor Platform</p>
      <h1>Tenant Login</h1>
      <el-form :model="form" label-position="top" @submit.prevent="handleSubmit">
        <el-form-item label="Tenant Slug">
          <el-input v-model="form.tenantSlug" placeholder="default" />
        </el-form-item>
        <el-form-item label="Email">
          <el-input v-model="form.identifier" placeholder="admin@example.local" />
        </el-form-item>
        <el-form-item label="Password">
          <el-input v-model="form.password" show-password type="password" />
        </el-form-item>
        <el-alert v-if="error" :closable="false" show-icon title="登录失败" :description="error" type="error" />
        <el-button class="submit" native-type="submit" type="primary" :loading="isSubmitting">登录</el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { useAuthStore } from "../stores/auth";

const router = useRouter();
const authStore = useAuthStore();
const isSubmitting = ref(false);
const error = ref("");
const form = reactive({
  tenantSlug: "default",
  identifier: "admin@example.local",
  password: "ChangeMe123!",
});

async function handleSubmit() {
  isSubmitting.value = true;
  error.value = "";

  try {
    await authStore.login(form);
    await router.push("/");
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Unable to sign in";
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<style scoped>
.login-shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background:
    radial-gradient(circle at 20% 20%, rgba(75, 192, 192, 0.18), transparent 24%),
    radial-gradient(circle at 80% 10%, rgba(84, 156, 255, 0.22), transparent 24%),
    linear-gradient(180deg, #081423 0%, #101928 100%);
}

.card {
  width: min(100%, 440px);
  padding: 32px;
  border-radius: 28px;
  background: rgba(10, 17, 28, 0.96);
  border: 1px solid rgba(143, 163, 191, 0.24);
}

.eyebrow {
  margin: 0 0 8px;
  color: #8fa3bf;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 12px;
}

h1 {
  margin: 0 0 24px;
}

.submit {
  margin-top: 16px;
  width: 100%;
}
</style>
