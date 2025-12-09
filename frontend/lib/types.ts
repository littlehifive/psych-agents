export type ChatRole = "system" | "user" | "assistant";

export interface AgentTrace {
  agent_key: string;
  agent_label: string;
  output: string;
  started_at: string;
  completed_at: string;
  duration_ms?: number;
  metadata?: Record<string, unknown>;
}

export interface CouncilSections {
  problem_framing?: string;
  theory_council_debate?: string;
  intervention_mapping_guide?: string;
  recommended_intervention_concepts?: string;
  [key: string]: string | undefined;
}

export interface CouncilResult {
  raw_problem: string;
  framed_problem?: string | null;
  im_summary?: string | null;
  theory_outputs: Record<string, string>;
  debate_summary?: string | null;
  theory_ranking?: string | null;
  final_synthesis: string;
  sections: CouncilSections;
  agent_traces: AgentTrace[];
}

export interface ChatMessage {
  role: ChatRole;
  content: string;
}

export interface ConversationResponse {
  session_id: string;
  mode: "chat" | "agent";
  assistant_message: ChatMessage;
  messages: ChatMessage[];
  agent_result?: CouncilResult;
  run_id?: string | null;
  auto_disable_agent?: boolean;
}

export interface ConversationRequestPayload {
  messages: ChatMessage[];
  agent_enabled: boolean;
  session_id?: string;
}

