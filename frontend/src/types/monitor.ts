export type MetricKey =
  | "cpu"
  | "memory"
  | "disk"
  | "gpu"
  | "gpu_memory_used"
  | "gpu_memory_utilization"
  | "gpu_utilization"
  | "gpu_temperature"
  | "gpu_power_usage";
export type RangeKey = "1h" | "6h" | "24h";
export type StepKey = "30s" | "1m";

export interface OverviewItem {
  metric: MetricKey;
  label: string;
  value: number;
  unit: string;
}

export interface OverviewResponse {
  generatedAt: string;
  items: OverviewItem[];
}

export interface GpuDevice {
  id: string;
  name: string;
  uuid: string;
  memoryUsedMiB: number;
  memoryTotalMiB: number;
  memoryUtilizationPercent: number;
  utilizationPercent: number;
  temperatureCelsius: number;
  powerUsageWatts: number;
  status: string;
}

export interface GpuDeviceListResponse {
  generatedAt: string;
  items: GpuDevice[];
}

export interface TimeseriesPoint {
  timestamp: string;
  value: number;
  unit: string;
}

export interface TimeseriesResponse {
  metric: MetricKey;
  range: RangeKey;
  step: StepKey;
  series: TimeseriesPoint[];
}
