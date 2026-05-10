import { http } from "./http";
import type { RangeKey, StepKey } from "../types/monitor";
import type {
  ModelMonitorMetricKey,
  ModelListResponse,
  ModelMonitorOverviewResponse,
  ModelMonitorTimeseriesResponse,
} from "../types/modelMonitor";

export async function fetchModelMonitorOverview() {
  const { data } = await http.get<ModelMonitorOverviewResponse>("/model-monitor/overview");
  return data;
}

export async function fetchModelList() {
  const { data } = await http.get<ModelListResponse>("/model-monitor/models");
  return data;
}

export async function fetchModelMonitorTimeseries(metric: ModelMonitorMetricKey, range: RangeKey, step: StepKey) {
  const { data } = await http.get<ModelMonitorTimeseriesResponse>("/model-monitor/timeseries", {
    params: { metric, range, step },
  });
  return data;
}
