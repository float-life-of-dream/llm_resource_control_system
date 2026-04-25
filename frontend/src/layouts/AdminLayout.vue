<template>
  <div class="shell">
    <aside class="sidebar">
      <div>
        <p class="brand">AI Monitor</p>
        <p class="tenant">{{ authStore.tenant?.name }}</p>
      </div>
      <nav class="nav">
        <RouterLink to="/">Dashboard</RouterLink>
        <RouterLink v-if="canManageTenant" to="/tenant/members">Members</RouterLink>
        <RouterLink v-if="canManageTenant" to="/tenant/settings">Tenant Settings</RouterLink>
        <RouterLink to="/sessions">My Sessions</RouterLink>
        <RouterLink v-if="authStore.isSystemAdmin" to="/system/tenants">System Tenants</RouterLink>
      </nav>
      <div class="sidebar-footer">
        <span>{{ authStore.user?.fullName }}</span>
        <el-button text type="danger" @click="handleLogout">Logout</el-button>
      </div>
    </aside>
    <main class="content">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";

import { useAuthStore } from "../stores/auth";

const authStore = useAuthStore();
const router = useRouter();
const canManageTenant = computed(() => ["owner", "admin"].includes(authStore.membershipRole ?? ""));

async function handleLogout() {
  await authStore.logout();
  await router.push("/login");
}
</script>

<style scoped>
.shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 280px 1fr;
  background:
    radial-gradient(circle at top left, rgba(84, 156, 255, 0.14), transparent 32%),
    linear-gradient(180deg, #06111f 0%, #0d1421 100%);
  color: #f5f7fb;
}

.sidebar {
  padding: 28px;
  border-right: 1px solid rgba(143, 163, 191, 0.14);
  background: rgba(5, 11, 18, 0.72);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.brand {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: #8fa3bf;
  font-size: 12px;
}

.tenant {
  margin: 12px 0 0;
  font-size: 24px;
  font-weight: 700;
}

.nav {
  display: grid;
  gap: 12px;
  margin-top: 24px;
}

.nav a {
  color: #d7e4f6;
  text-decoration: none;
}

.nav a.router-link-active {
  color: #4bc0c0;
}

.sidebar-footer {
  display: grid;
  gap: 8px;
}

.content {
  padding: 40px 20px 64px;
  max-width: 1320px;
  width: 100%;
}

@media (max-width: 960px) {
  .shell {
    grid-template-columns: 1fr;
  }
}
</style>
