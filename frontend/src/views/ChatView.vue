<template>
  <AdminLayout>
    <section class="chat-page">
      <aside class="session-panel">
        <div class="panel-head">
          <div>
            <span class="eyebrow">Ollama</span>
            <h1>Chat</h1>
          </div>
          <el-button type="primary" @click="newSession">New</el-button>
        </div>

        <div class="session-list">
          <button
            v-for="session in store.sessions"
            :key="session.id"
            class="session-item"
            :class="{ active: session.id === store.activeSession?.id }"
            @click="store.loadSession(session.id)"
          >
            <span>{{ session.title }}</span>
            <small>{{ session.model }}</small>
          </button>
        </div>
      </aside>

      <section class="chat-panel">
        <div class="chat-head">
          <div>
            <span class="eyebrow">Current session</span>
            <h2>{{ store.activeSession?.title ?? "New chat" }}</h2>
          </div>
          <el-button v-if="store.activeSession" text type="danger" @click="removeSession">Delete</el-button>
        </div>

        <el-alert
          v-if="store.error"
          title="Chat failed"
          :description="store.error"
          type="error"
          show-icon
          :closable="false"
        />

        <div class="messages">
          <div v-if="!store.messages.length" class="empty-state">
            Ask a question. Requests are routed through ollama-exporter so `/models` reflects chat traffic.
          </div>
          <article v-for="message in store.messages" :key="message.id" class="message" :class="message.role">
            <span>{{ message.role }}</span>
            <p>{{ message.content || (store.isStreaming && message.role === "assistant" ? "Thinking..." : "") }}</p>
          </article>
        </div>

        <form class="composer" @submit.prevent="send">
          <el-input
            v-model="draft"
            type="textarea"
            :rows="3"
            resize="none"
            placeholder="Ask about your AI runtime, logs, models, or operations..."
            :disabled="store.isStreaming"
            @keydown.enter.exact.prevent="send"
          />
          <el-button type="primary" native-type="submit" :loading="store.isStreaming" :disabled="!draft.trim()">
            Send
          </el-button>
        </form>
      </section>
    </section>
  </AdminLayout>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import AdminLayout from "../layouts/AdminLayout.vue";
import { useChatStore } from "../stores/chat";

const store = useChatStore();
const draft = ref("");

onMounted(() => {
  void store.loadSessions();
});

async function newSession() {
  await store.createSession();
}

async function removeSession() {
  if (!store.activeSession) {
    return;
  }
  await store.deleteSession(store.activeSession.id);
}

async function send() {
  const content = draft.value;
  draft.value = "";
  try {
    await store.sendMessage(content);
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "Failed to send message");
  }
}
</script>

<style scoped>
.chat-page {
  min-height: calc(100vh - 104px);
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 20px;
}

.session-panel,
.chat-panel {
  background: rgba(13, 20, 33, 0.98);
  border: 1px solid rgba(143, 163, 191, 0.18);
  border-radius: 24px;
  padding: 20px;
}

.session-panel {
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 16px;
}

.panel-head,
.chat-head,
.composer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.eyebrow {
  color: #8fa3bf;
}

h1,
h2 {
  margin: 6px 0 0;
}

.session-list {
  display: grid;
  align-content: start;
  gap: 10px;
  overflow: auto;
}

.session-item {
  border: 1px solid rgba(143, 163, 191, 0.16);
  border-radius: 14px;
  padding: 14px;
  text-align: left;
  color: #d7e4f6;
  background: rgba(7, 14, 24, 0.9);
  cursor: pointer;
}

.session-item.active {
  border-color: #4bc0c0;
}

.session-item span,
.session-item small {
  display: block;
}

.session-item small {
  margin-top: 6px;
  color: #8fa3bf;
}

.chat-panel {
  display: grid;
  grid-template-rows: auto auto 1fr auto;
  gap: 16px;
  min-width: 0;
}

.messages {
  display: grid;
  align-content: start;
  gap: 14px;
  overflow: auto;
  min-height: 420px;
  padding: 8px;
}

.message {
  max-width: 78%;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(7, 14, 24, 0.9);
  border: 1px solid rgba(143, 163, 191, 0.12);
}

.message.user {
  justify-self: end;
  background: rgba(75, 192, 192, 0.14);
}

.message span {
  display: block;
  margin-bottom: 8px;
  color: #8fa3bf;
  text-transform: capitalize;
}

.message p {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.6;
}

.empty-state {
  min-height: 240px;
  display: grid;
  place-items: center;
  color: #8fa3bf;
  border: 1px dashed rgba(143, 163, 191, 0.3);
  border-radius: 18px;
  text-align: center;
  padding: 24px;
}

.composer {
  align-items: stretch;
}

.composer :deep(.el-textarea) {
  flex: 1;
}

@media (max-width: 960px) {
  .chat-page {
    grid-template-columns: 1fr;
  }
}
</style>
