import { API_BASE_URL, getAccessToken, http } from "./http";
import type { ChatSession, ChatSessionDetailResponse, ChatSessionListResponse } from "../types/chat";

export async function createChatSession(payload: { model?: string; title?: string }) {
  const { data } = await http.post<ChatSession>("/chat/sessions", payload);
  return data;
}

export async function fetchChatSessions() {
  const { data } = await http.get<ChatSessionListResponse>("/chat/sessions");
  return data;
}

export async function fetchChatSession(sessionId: string) {
  const { data } = await http.get<ChatSessionDetailResponse>(`/chat/sessions/${sessionId}`);
  return data;
}

export async function deleteChatSession(sessionId: string) {
  await http.delete(`/chat/sessions/${sessionId}`);
}

export async function streamChatMessage(
  sessionId: string,
  message: string,
  handlers: {
    onMessage: (content: string) => void;
    onDone: () => void;
    onError: (message: string) => void;
  },
) {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getAccessToken() ?? ""}`,
    },
    body: JSON.stringify({ message }),
  });

  if (!response.ok || !response.body) {
    throw new Error(`Chat request failed with status ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";
    for (const eventText of events) {
      const event = parseSseEvent(eventText);
      if (event.event === "message") {
        handlers.onMessage(String(event.data.content ?? ""));
      } else if (event.event === "done") {
        handlers.onDone();
      } else if (event.event === "error") {
        handlers.onError(String(event.data.message ?? "Chat stream failed"));
      }
    }
  }
}

function parseSseEvent(eventText: string) {
  const lines = eventText.split("\n");
  const event = lines.find((line) => line.startsWith("event:"))?.slice("event:".length).trim() ?? "message";
  const data = lines
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice("data:".length).trim())
    .join("\n");
  return {
    event,
    data: data ? (JSON.parse(data) as Record<string, unknown>) : {},
  };
}
