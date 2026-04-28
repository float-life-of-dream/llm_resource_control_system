import { http } from "./http";
import type {
  AnalysisDetail,
  AnalysisHistoryResponse,
  AnalysisRunPayload,
  AnalysisRunResponse,
} from "../types/analysis";

export async function runAnalysis(payload: AnalysisRunPayload) {
  const { data } = await http.post<AnalysisRunResponse>("/analysis/run", payload);
  return data;
}

export async function fetchAnalysisHistory() {
  const { data } = await http.get<AnalysisHistoryResponse>("/analysis/history");
  return data;
}

export async function fetchAnalysisDetail(analysisId: string) {
  const { data } = await http.get<AnalysisDetail>(`/analysis/history/${analysisId}`);
  return data;
}
