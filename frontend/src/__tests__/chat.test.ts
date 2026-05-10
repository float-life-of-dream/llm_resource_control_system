import { describe, expect, it, vi } from "vitest";

import { createChatSession, fetchChatSessions, streamChatMessage } from "../api/chat";
import { http } from "../api/http";

vi.mock("../api/http", () => ({
  API_BASE_URL: "/api",
  getAccessToken: () => "token",
  http: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

describe("chat api", () => {
  it("creates chat sessions", async () => {
    vi.mocked(http.post).mockResolvedValueOnce({ data: { id: "c1", title: "New chat", model: "llama3.1:8b" } });

    const response = await createChatSession({});

    expect(http.post).toHaveBeenCalledWith("/chat/sessions", {});
    expect(response.id).toBe("c1");
  });

  it("fetches chat sessions", async () => {
    vi.mocked(http.get).mockResolvedValueOnce({ data: { items: [] } });

    const response = await fetchChatSessions();

    expect(http.get).toHaveBeenCalledWith("/chat/sessions");
    expect(response.items).toEqual([]);
  });

  it("parses sse stream chunks", async () => {
    const encoder = new TextEncoder();
    const body = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('event: message\ndata: {"content":"hi"}\n\n'));
        controller.enqueue(encoder.encode('event: done\ndata: {}\n\n'));
        controller.close();
      },
    });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        body,
      }),
    );
    const chunks: string[] = [];

    await streamChatMessage("c1", "hello", {
      onMessage: (content) => chunks.push(content),
      onDone: vi.fn(),
      onError: vi.fn(),
    });

    expect(chunks).toEqual(["hi"]);
    expect(fetch).toHaveBeenCalledWith(
      "/api/chat/sessions/c1/stream",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ Authorization: "Bearer token" }),
      }),
    );
  });
});
