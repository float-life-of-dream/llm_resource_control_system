export interface ChatSession {
  id: string;
  title: string;
  model: string;
  createdAt: string;
  updatedAt: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  rawMetadata: Record<string, unknown>;
  createdAt: string;
}

export interface ChatSessionListResponse {
  items: ChatSession[];
}

export interface ChatSessionDetailResponse {
  session: ChatSession;
  messages: ChatMessage[];
}
