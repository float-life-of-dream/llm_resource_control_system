import { http } from "./http";
import type { Membership, TenantProfile, TenantRole } from "../types/auth";

export async function fetchSystemTenants() {
  const { data } = await http.get<{ items: TenantProfile[] }>("/system/tenants");
  return data;
}

export async function createSystemTenant(payload: { name: string; slug: string }) {
  const { data } = await http.post<TenantProfile>("/system/tenants", payload);
  return data;
}

export async function createSystemTenantMember(
  tenantId: string,
  payload: { email: string; fullName: string; password: string; role: TenantRole },
) {
  const { data } = await http.post<Membership>(`/system/tenants/${tenantId}/members`, payload);
  return data;
}
