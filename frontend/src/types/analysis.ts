import type { TenantProfile, UserProfile } from "./auth";
import type { RangeKey } from "./monitor";

export interface AnalysisRunPayload {
  range: RangeKey;
  logQuery: string;
  logLimit: number;
  includeMetrics: boolean;
}

export interface AnalysisEvidenceSummary {
  metrics: string[];
  logCount: number;
}

export interface AnalysisRunResponse {
  analysisId: string;
  status: string;
  summary: string;
  anomalies: string[];
  recommendations: string[];
  evidenceSummary: AnalysisEvidenceSummary;
  model: string;
  durationMs: number;
}

export interface AnalysisHistoryItem {
  analysisId: string;
  status: string;
  range: RangeKey;
  logQuery?: string | null;
  logLimit: number;
  includeMetrics: boolean;
  model: string;
  durationMs?: number | null;
  errorMessage?: string | null;
  createdAt: string;
  completedAt?: string | null;
  summary: string;
  evidenceSummary: AnalysisEvidenceSummary;
}

export interface AnalysisHistoryResponse {
  items: AnalysisHistoryItem[];
}

export interface AnalysisEvidence {
  metricsSnapshot: Record<
    string,
    {
      label: string;
      unit: string;
      current: number;
      min: number;
      max: number;
      avg: number;
      threshold?: number | null;
      thresholdExceeded: boolean;
    }
  >;
  logExcerpt: Array<{
    timestamp: string;
    level: string;
    service: string;
    message: string;
  }>;
}

export interface AnalysisDetail extends AnalysisHistoryItem {
  anomalies: string[];
  recommendations: string[];
  rawModelOutput: string;
  user: UserProfile;
  tenant: TenantProfile;
  evidence: AnalysisEvidence;
}
