<template>
  <section class="analysis-card">
    <div class="analysis-head">
      <div>
        <p class="eyebrow">Ollama Analysis</p>
        <h2>AI Analysis</h2>
      </div>
      <div class="actions">
        <el-button text @click="openHistory">History</el-button>
        <el-button type="primary" :loading="analysisStore.isRunning" :disabled="analysisStore.isRunning" @click="submit">
          Start Analysis
        </el-button>
      </div>
    </div>

    <div class="controls">
      <el-input v-model="form.logQuery" placeholder="Keyword filter for Elasticsearch logs" clearable />
      <el-input-number v-model="form.logLimit" :min="1" :max="200" />
    </div>

    <el-alert
      v-if="analysisStore.error"
      title="Analysis failed"
      :description="analysisStore.error"
      type="error"
      show-icon
      :closable="false"
    />

    <div v-if="analysisStore.isRunning" class="state-panel">Analyzing metrics and logs...</div>

    <div v-else-if="analysisStore.current" class="result-grid">
      <div class="result-block">
        <span class="label">Summary</span>
        <p>{{ analysisStore.current.summary }}</p>
      </div>
      <div class="result-block">
        <span class="label">Anomalies</span>
        <ul>
          <li v-for="item in analysisStore.current.anomalies" :key="item">{{ item }}</li>
        </ul>
      </div>
      <div class="result-block">
        <span class="label">Recommendations</span>
        <ul>
          <li v-for="item in analysisStore.current.recommendations" :key="item">{{ item }}</li>
        </ul>
      </div>
      <div class="meta-row">
        <span>Model: {{ analysisStore.current.model }}</span>
        <span>Duration: {{ analysisStore.current.durationMs }} ms</span>
        <span>Logs: {{ analysisStore.current.evidenceSummary.logCount }}</span>
      </div>
    </div>
    <div v-else class="state-panel">Run a manual Ollama analysis for the current monitoring range.</div>

    <el-drawer v-model="historyVisible" title="Analysis History" size="50%">
      <div class="history-layout">
        <el-table :data="analysisStore.history" v-loading="analysisStore.isHistoryLoading">
          <el-table-column prop="createdAt" label="Created" />
          <el-table-column prop="status" label="Status" width="120" />
          <el-table-column prop="model" label="Model" />
          <el-table-column prop="summary" label="Summary" />
          <el-table-column label="Actions" width="120">
            <template #default="{ row }">
              <el-button link type="primary" @click="loadDetail(row.analysisId)">Detail</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="detail-panel">
          <div v-if="analysisStore.detail" class="detail-body">
            <h3>{{ analysisStore.detail.summary || "Analysis Detail" }}</h3>
            <p class="detail-meta">
              {{ analysisStore.detail.model }} · {{ analysisStore.detail.durationMs ?? 0 }} ms · {{ analysisStore.detail.user.email }}
            </p>
            <div class="detail-section">
              <span class="label">Anomalies</span>
              <ul>
                <li v-for="item in analysisStore.detail.anomalies" :key="item">{{ item }}</li>
              </ul>
            </div>
            <div class="detail-section">
              <span class="label">Recommendations</span>
              <ul>
                <li v-for="item in analysisStore.detail.recommendations" :key="item">{{ item }}</li>
              </ul>
            </div>
            <div class="detail-section">
              <span class="label">Metrics Snapshot</span>
              <pre>{{ JSON.stringify(analysisStore.detail.evidence.metricsSnapshot, null, 2) }}</pre>
            </div>
            <div class="detail-section">
              <span class="label">Log Excerpt</span>
              <pre>{{ JSON.stringify(analysisStore.detail.evidence.logExcerpt, null, 2) }}</pre>
            </div>
          </div>
          <div v-else class="state-panel small">Select a history item to inspect retained evidence.</div>
        </div>
      </div>
    </el-drawer>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import { useAnalysisStore } from "../stores/analysis";
import type { RangeKey } from "../types/monitor";

const props = defineProps<{
  range: RangeKey;
}>();

const analysisStore = useAnalysisStore();
const historyVisible = ref(false);
const form = reactive({
  logQuery: "",
  logLimit: 50,
  includeMetrics: true,
});

async function submit() {
  try {
    await analysisStore.run({
      range: props.range,
      logQuery: form.logQuery,
      logLimit: form.logLimit,
      includeMetrics: form.includeMetrics,
    });
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "Failed to run analysis.");
  }
}

async function openHistory() {
  historyVisible.value = true;
  await analysisStore.loadHistory();
}

async function loadDetail(analysisId: string) {
  try {
    await analysisStore.loadDetail(analysisId);
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "Failed to load analysis detail.");
  }
}
</script>

<style scoped>
.analysis-card {
  display: grid;
  gap: 20px;
  padding: 24px;
  background: linear-gradient(180deg, rgba(18, 31, 50, 0.98), rgba(9, 17, 27, 0.98));
  border: 1px solid rgba(143, 163, 191, 0.18);
  border-radius: 24px;
}

.analysis-head,
.actions,
.controls,
.meta-row {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
}

.controls {
  justify-content: flex-start;
}

.controls :deep(.el-input) {
  max-width: 420px;
}

.eyebrow,
.label,
.detail-meta {
  color: #8fa3bf;
}

.result-grid,
.detail-body {
  display: grid;
  gap: 16px;
}

.result-block,
.detail-section {
  padding: 16px;
  border-radius: 18px;
  background: rgba(7, 14, 24, 0.9);
  border: 1px solid rgba(143, 163, 191, 0.12);
}

.meta-row {
  justify-content: flex-start;
  color: #8fa3bf;
  flex-wrap: wrap;
}

.history-layout {
  display: grid;
  gap: 20px;
}

.detail-panel pre {
  white-space: pre-wrap;
  word-break: break-word;
}

.state-panel {
  min-height: 140px;
  display: grid;
  place-items: center;
  border-radius: 18px;
  border: 1px dashed rgba(143, 163, 191, 0.3);
  color: #8fa3bf;
}

.state-panel.small {
  min-height: 100px;
}

@media (max-width: 900px) {
  .analysis-head,
  .controls {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
