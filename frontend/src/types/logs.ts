import type { RangeKey } from "./monitor";

export type LogLevel = "" | "error" | "warn" | "info" | "debug";

export interface LogItem {
  timestamp: string;
  level: string;
  service: string;
  message: string;
  traceId: string;
  host: string;
  source: string;
}

export interface LogSearchParams {
  range: RangeKey;
  query: string;
  level: LogLevel;
  service: string;
  limit: number;
}

export interface LogSearchResponse {
  generatedAt: string;
  range: RangeKey;
  total: number;
  items: LogItem[];
}

export interface LogBucket {
  key: string;
  count: number;
}

export interface LogSummaryResponse {
  generatedAt: string;
  total: number;
  levels: LogBucket[];
  services: LogBucket[];
}

export interface LogServicesResponse {
  generatedAt: string;
  items: string[];
}
