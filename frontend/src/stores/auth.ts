import { defineStore } from "pinia";

import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "../api/http";
import { fetchMe, login as loginRequest, logout as logoutRequest } from "../api/auth";
import type { TenantProfile, TenantRole, UserProfile } from "../types/auth";

const USER_KEY = "ai-monitor.user";
const TENANT_KEY = "ai-monitor.tenant";
const ROLE_KEY = "ai-monitor.role";

function readJson<T>(key: string): T | null {
  const value = localStorage.getItem(key);
  return value ? (JSON.parse(value) as T) : null;
}

export const useAuthStore = defineStore("auth", {
  state: () => ({
    accessToken: getAccessToken() ?? "",
    refreshToken: getRefreshToken() ?? "",
    user: readJson<UserProfile>(USER_KEY),
    tenant: readJson<TenantProfile>(TENANT_KEY),
    membershipRole: (localStorage.getItem(ROLE_KEY) as TenantRole | null) ?? null,
    isReady: false,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken && state.user && state.tenant),
    isSystemAdmin: (state) => Boolean(state.user?.isSystemAdmin),
  },
  actions: {
    persist(payload: {
      accessToken: string;
      refreshToken: string;
      user: UserProfile;
      tenant: TenantProfile;
      membershipRole: TenantRole;
    }) {
      this.accessToken = payload.accessToken;
      this.refreshToken = payload.refreshToken;
      this.user = payload.user;
      this.tenant = payload.tenant;
      this.membershipRole = payload.membershipRole;
      setTokens(payload.accessToken, payload.refreshToken);
      localStorage.setItem(USER_KEY, JSON.stringify(payload.user));
      localStorage.setItem(TENANT_KEY, JSON.stringify(payload.tenant));
      localStorage.setItem(ROLE_KEY, payload.membershipRole);
    },
    clear() {
      this.accessToken = "";
      this.refreshToken = "";
      this.user = null;
      this.tenant = null;
      this.membershipRole = null;
      clearTokens();
      localStorage.removeItem(USER_KEY);
      localStorage.removeItem(TENANT_KEY);
      localStorage.removeItem(ROLE_KEY);
    },
    async login(payload: { tenantSlug: string; identifier: string; password: string }) {
      const auth = await loginRequest(payload);
      this.persist(auth);
      this.isReady = true;
    },
    async initialize() {
      if (!this.accessToken || !this.refreshToken) {
        this.isReady = true;
        return;
      }

      try {
        const me = await fetchMe();
        this.user = me.user;
        this.tenant = me.tenant;
        this.membershipRole = me.membershipRole;
        localStorage.setItem(USER_KEY, JSON.stringify(me.user));
        localStorage.setItem(TENANT_KEY, JSON.stringify(me.tenant));
        localStorage.setItem(ROLE_KEY, me.membershipRole);
      } catch {
        this.clear();
      } finally {
        this.isReady = true;
      }
    },
    async logout() {
      try {
        if (this.accessToken) {
          await logoutRequest();
        }
      } finally {
        this.clear();
      }
    },
  },
});
