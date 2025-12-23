export type ChatRole = "system" | "user" | "assistant";

export interface ChatMessage {
  role: ChatRole;
  content: string;
}

export interface ConversationResponse {
  session_id: string;
  assistant_message: ChatMessage;
  messages: ChatMessage[];
}

export interface StoredConversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  updatedAt: number;
}

export interface LibraryItem {
  id: string;
  question: string;
  answer: string;
  citations?: string;
  title: string;
  summary: string;
  theme: string;
  tags: string[];
  createdAt: number;
}

export interface ConversationRequestPayload {
  messages: ChatMessage[];
  session_id?: string;
}
