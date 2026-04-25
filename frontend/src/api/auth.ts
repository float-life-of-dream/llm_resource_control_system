import { http } from "./http";
import type { AuthPayload, SessionItem } from "../types/auth";

export async function login(payload: { tenantSlug: string; identifier: string; password: string }) {
  const { data } = await http.post<AuthPayload>("/auth/login", payload);
  return data;
}

export async function refresh(refreshToken: string) {
  const { data } = await http.post<AuthPayload>("/auth/refresh", { refreshToken });
  return data;
}

export async function fetchMe() {
  const { data } = await http.get<Pick<AuthPayload, "user" | "tenant" | "membershipRole">>("/auth/me");
  return data;
}

export async function logout() {
  await http.post("/auth/logout");
}

export async function fetchSessions() {
  const { data } = await http.get<{ items: SessionItem[] }>("/auth/sessions");
  return data;
}

export async function revokeSession(sessionId: string) {
  await http.delete(`/auth/sessions/${sessionId}`);
}
