export type TenantRole = "owner" | "admin" | "viewer";

export interface UserProfile {
  id: string;
  email: string;
  fullName: string;
  isSystemAdmin: boolean;
}

export interface TenantProfile {
  id: string;
  name: string;
  slug: string;
}

export interface AuthPayload {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  user: UserProfile;
  tenant: TenantProfile;
  membershipRole: TenantRole;
}

export interface SessionItem {
  id: string;
  tenantId: string;
  userAgent?: string | null;
  ipAddress?: string | null;
  expiresAt: string;
  createdAt: string;
  lastUsedAt: string;
  revokedAt?: string | null;
}

export interface Membership {
  id: string;
  role: TenantRole;
  user: UserProfile;
  tenant: TenantProfile;
}
