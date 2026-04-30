import { createRouter, createWebHistory } from "vue-router";

import DashboardView from "../views/DashboardView.vue";
import LoginView from "../views/LoginView.vue";
import ModelMonitorView from "../views/ModelMonitorView.vue";
import SessionsView from "../views/SessionsView.vue";
import SystemTenantsView from "../views/SystemTenantsView.vue";
import TenantMembersView from "../views/TenantMembersView.vue";
import TenantSettingsView from "../views/TenantSettingsView.vue";
import { useAuthStore } from "../stores/auth";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", name: "login", component: LoginView, meta: { public: true } },
    { path: "/", name: "dashboard", component: DashboardView },
    { path: "/models", name: "model-monitor", component: ModelMonitorView },
    { path: "/tenant/members", name: "tenant-members", component: TenantMembersView, meta: { roles: ["owner", "admin"] } },
    { path: "/tenant/settings", name: "tenant-settings", component: TenantSettingsView, meta: { roles: ["owner", "admin"] } },
    { path: "/sessions", name: "sessions", component: SessionsView },
    { path: "/system/tenants", name: "system-tenants", component: SystemTenantsView, meta: { systemAdmin: true } },
  ],
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore();
  if (!authStore.isReady) {
    await authStore.initialize();
  }

  if (to.meta.public) {
    if (authStore.isAuthenticated && to.path === "/login") {
      return "/";
    }
    return true;
  }

  if (!authStore.isAuthenticated) {
    return "/login";
  }

  if ((to.meta.systemAdmin as boolean | undefined) && !authStore.isSystemAdmin) {
    return "/";
  }

  const allowedRoles = to.meta.roles as string[] | undefined;
  if (allowedRoles && !allowedRoles.includes(authStore.membershipRole ?? "")) {
    return "/";
  }

  return true;
});
