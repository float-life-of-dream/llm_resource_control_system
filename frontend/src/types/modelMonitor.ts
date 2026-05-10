import type { RangeKey, StepKey, TimeseriesPoint } from "./monitor";

export type ModelMonitorMetricKey =
  | "request_rate"
  | "latency"
  | "concurrency"
  | "tokens_per_second"
  | "error_rate"
  | "loaded_models";

export interface ModelMonitorOverviewItem {
  metric: string;
  label: string;
  value: number;
  unit: string;
}

export interface ModelMonitorOverviewResponse {
  generatedAt: string;
  items: ModelMonitorOverviewItem[];
}

export interface ModelInfo {
  name: string;
  parameterSize: string | null;
  quantization: string | null;
  contextWindow: number | null;
  memoryBytes: number;
  status: string;
  lastSeenAt: string | null;
}

export interface ModelListResponse {
  generatedAt: string;
  items: ModelInfo[];
}

export interface ModelMonitorTimeseriesResponse {
  metric: ModelMonitorMetricKey;
  range: RangeKey;
  step: StepKey;
  series: TimeseriesPoint[];
}
