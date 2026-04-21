import { http } from "./http";
import type { MetricKey, OverviewResponse, RangeKey, StepKey, TimeseriesResponse } from "../types/monitor";

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
