import { http } from "./http";
import type { Membership, TenantProfile, TenantRole } from "../types/auth";

export async function fetchTenant() {
  const { data } = await http.get<TenantProfile>("/tenant");
  return data;
}

export async function updateTenant(name: string) {
  const { data } = await http.patch<TenantProfile>("/tenant", { name });
  return data;
}

export async function fetchTenantMembers() {
  const { data } = await http.get<{ items: Membership[] }>("/tenant/members");
  return data;
}

export async function createTenantMember(payload: {
  email: string;
  fullName: string;
  password: string;
  role: TenantRole;
}) {
  const { data } = await http.post<Membership>("/tenant/members", payload);
  return data;
}

export async function updateTenantMember(membershipId: string, role: TenantRole) {
  const { data } = await http.patch<Membership>(`/tenant/members/${membershipId}`, { role });
  return data;
}

export async function deleteTenantMember(membershipId: string) {
  await http.delete(`/tenant/members/${membershipId}`);
}
