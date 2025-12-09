import type {
  ConversationRequestPayload,
  ConversationResponse,
} from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_COUNCIL_API?.replace(/\/$/, "") ||
  "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `API ${path} failed (${response.status}): ${errorText || "Unknown error"}`,
    );
  }
  return (await response.json()) as T;
}

export async function sendConversation(
  payload: ConversationRequestPayload,
): Promise<ConversationResponse> {
  return request<ConversationResponse>("/conversation/send", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

