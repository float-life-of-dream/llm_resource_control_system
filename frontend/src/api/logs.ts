import { http } from "./http";
import type { LogSearchParams, LogSearchResponse, LogServicesResponse, LogSummaryResponse } from "../types/logs";
import type { RangeKey } from "../types/monitor";

export async function searchLogs(params: LogSearchParams) {
  const { data } = await http.get<LogSearchResponse>("/logs/search", { params });
  return data;
}

export async function fetchLogSummary(range: RangeKey, query = "") {
  const { data } = await http.get<LogSummaryResponse>("/logs/summary", { params: { range, query } });
  return data;
}

export async function fetchLogServices(range: RangeKey) {
  const { data } = await http.get<LogServicesResponse>("/logs/services", { params: { range } });
  return data;
}
