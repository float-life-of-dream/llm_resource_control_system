import { defineStore } from "pinia";

import {
  createChatSession,
  deleteChatSession,
  fetchChatSession,
  fetchChatSessions,
  streamChatMessage,
} from "../api/chat";
import type { ChatMessage, ChatSession } from "../types/chat";

function localMessage(role: ChatMessage["role"], content: string): ChatMessage {
  return {
    id: `local-${crypto.randomUUID()}`,
    role,
    content,
    rawMetadata: {},
    createdAt: new Date().toISOString(),
  };
}

export const useChatStore = defineStore("chat", {
  state: () => ({
    sessions: [] as ChatSession[],
    activeSession: null as ChatSession | null,
    messages: [] as ChatMessage[],
    isLoading: false,
    isStreaming: false,
    error: "",
  }),
  actions: {
    async loadSessions() {
      this.isLoading = true;
      this.error = "";
      try {
        const response = await fetchChatSessions();
        this.sessions = response.items;
        if (!this.activeSession && this.sessions.length) {
          await this.loadSession(this.sessions[0].id);
        }
      } catch (error) {
        this.error = error instanceof Error ? error.message : "Failed to load chat sessions";
      } finally {
        this.isLoading = false;
      }
    },
    async createSession() {
      const session = await createChatSession({});
      this.sessions = [session, ...this.sessions];
      this.activeSession = session;
      this.messages = [];
    },
    async loadSession(sessionId: string) {
      this.isLoading = true;
      this.error = "";
      try {
        const response = await fetchChatSession(sessionId);
        this.activeSession = response.session;
        this.messages = response.messages;
      } catch (error) {
        this.error = error instanceof Error ? error.message : "Failed to load chat session";
      } finally {
        this.isLoading = false;
      }
    },
    async deleteSession(sessionId: string) {
      await deleteChatSession(sessionId);
      this.sessions = this.sessions.filter((session) => session.id !== sessionId);
      if (this.activeSession?.id === sessionId) {
        this.activeSession = null;
        this.messages = [];
        if (this.sessions.length) {
          await this.loadSession(this.sessions[0].id);
        }
      }
    },
    async sendMessage(content: string) {
      const message = content.trim();
      if (!message || this.isStreaming) {
        return;
      }
      if (!this.activeSession) {
        await this.createSession();
      }
      if (!this.activeSession) {
        throw new Error("No active chat session");
      }

      this.error = "";
      this.isStreaming = true;
      this.messages.push(localMessage("user", message));
      const assistantMessage = localMessage("assistant", "");
      this.messages.push(assistantMessage);

      try {
        await streamChatMessage(this.activeSession.id, message, {
          onMessage: (chunk) => {
            assistantMessage.content += chunk;
          },
          onDone: () => undefined,
          onError: (errorMessage) => {
            throw new Error(errorMessage);
          },
        });
        await this.loadSessions();
        await this.loadSession(this.activeSession.id);
      } catch (error) {
        this.error = error instanceof Error ? error.message : "Failed to send chat message";
      } finally {
        this.isStreaming = false;
      }
    },
  },
});
