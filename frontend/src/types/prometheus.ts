export interface PrometheusHealthResponse {
  status: string;
  baseUrl: string;
  generatedAt: string;
}

export interface PrometheusTarget {
  job: string;
  instance: string;
  health: string;
  scrapeUrl: string;
  lastScrape: string | null;
  lastError: string;
}

export interface PrometheusTargetsResponse {
  generatedAt: string;
  items: PrometheusTarget[];
}

export interface PrometheusMetric {
  key: string;
  label: string;
  unit: string;
}

export interface PrometheusMetricGroup {
  key: string;
  label: string;
  items: PrometheusMetric[];
}

export interface PrometheusMetricsResponse {
  generatedAt: string;
  groups: PrometheusMetricGroup[];
}
