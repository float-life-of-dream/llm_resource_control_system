import { beforeEach, describe, expect, it, vi } from "vitest";
import { setActivePinia, createPinia } from "pinia";

import { useAuthStore } from "../stores/auth";

vi.mock("../api/auth", () => ({
  login: vi.fn().mockResolvedValue({
    accessToken: "access-token",
    refreshToken: "refresh-token",
    expiresIn: 900,
    user: { id: "u1", email: "admin@example.local", fullName: "Admin", isSystemAdmin: true },
    tenant: { id: "t1", name: "Default Tenant", slug: "default" },
    membershipRole: "owner",
  }),
  fetchMe: vi.fn().mockResolvedValue({
    user: { id: "u1", email: "admin@example.local", fullName: "Admin", isSystemAdmin: true },
    tenant: { id: "t1", name: "Default Tenant", slug: "default" },
    membershipRole: "owner",
  }),
  logout: vi.fn().mockResolvedValue(undefined),
}));

const storage = new Map<string, string>();

vi.stubGlobal("localStorage", {
  getItem: vi.fn((key: string) => storage.get(key) ?? null),
  setItem: vi.fn((key: string, value: string) => {
    storage.set(key, value);
  }),
  removeItem: vi.fn((key: string) => {
    storage.delete(key);
  }),
  clear: vi.fn(() => {
    storage.clear();
  }),
});

describe("auth store", () => {
  beforeEach(() => {
    localStorage.clear();
    setActivePinia(createPinia());
  });

  it("persists login payload", async () => {
    const store = useAuthStore();
    await store.login({
      tenantSlug: "default",
      identifier: "admin@example.local",
      password: "ChangeMe123!",
    });

    expect(store.isAuthenticated).toBe(true);
    expect(store.tenant?.slug).toBe("default");
  });
});
