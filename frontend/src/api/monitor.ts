import { http } from "./http";
import type {
  GpuDeviceListResponse,
  MetricKey,
  OverviewResponse,
  RangeKey,
  StepKey,
  TimeseriesResponse,
} from "../types/monitor";

export async function fetchOverview() {
  const { data } = await http.get<OverviewResponse>("/monitor/overview");
  return data;
}

export async function fetchTimeseries(metric: MetricKey, range: RangeKey, step: StepKey) {
  const { data } = await http.get<TimeseriesResponse>("/monitor/timeseries", {
    params: { metric, range, step },
  });
  return data;
}

export async function fetchGpuDevices() {
  const { data } = await http.get<GpuDeviceListResponse>("/monitor/gpus");
  return data;
}
