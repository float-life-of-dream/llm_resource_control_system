import { http } from "./http";
import type {
  PrometheusHealthResponse,
  PrometheusMetricsResponse,
  PrometheusTargetsResponse,
} from "../types/prometheus";

export async function fetchPrometheusHealth() {
  const { data } = await http.get<PrometheusHealthResponse>("/prometheus/health");
  return data;
}

export async function fetchPrometheusTargets() {
  const { data } = await http.get<PrometheusTargetsResponse>("/prometheus/targets");
  return data;
}

export async function fetchPrometheusMetrics() {
  const { data } = await http.get<PrometheusMetricsResponse>("/prometheus/metrics");
  return data;
}
