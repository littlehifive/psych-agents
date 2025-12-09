"use client";

import { useMemo, useState } from "react";
import AgentToggle from "@/components/agent-toggle";
import ChatComposer from "@/components/chat-composer";
import AgentFlowVisualizer from "@/components/agent-flow-visualizer";
import { sendConversation } from "@/lib/api";
import type { ChatMessage, CouncilResult } from "@/lib/types";

const INITIAL_ASSISTANT_MESSAGE: ChatMessage = {
  role: "assistant",
  content:
    "Hi! I’m the Theory Council Studio. Ask anything about your intervention challenge. Flip the Agent toggle if you want the full multi-agent workflow.",
};

export default function ConversationPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    INITIAL_ASSISTANT_MESSAGE,
  ]);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [agentEnabled, setAgentEnabled] = useState(false);
  const [agentResult, setAgentResult] = useState<CouncilResult | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const visibleMessages = useMemo(
    () => messages.filter((message) => message.role !== "system"),
    [messages],
  );

  const handleSend = async (content: string) => {
    const pendingMessages = [...messages, { role: "user", content }];
    setMessages(pendingMessages);
    setIsSending(true);
    setError(null);
    try {
      const response = await sendConversation({
        messages: pendingMessages,
        agent_enabled: agentEnabled,
        session_id: sessionId,
      });
      setSessionId(response.session_id);
      setMessages(response.messages);
      if (response.agent_result) {
        setAgentResult(response.agent_result);
        setRunId(response.run_id ?? null);
      } else {
        setAgentResult(null);
        setRunId(null);
      }
      if (response.auto_disable_agent) {
        setAgentEnabled(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to send message.");
    } finally {
      setIsSending(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-8 px-6 py-10">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brand-600">
            Theory Council Studio
          </p>
          <h1 className="text-3xl font-bold text-slate-900">
            Continuous Conversation + Agent Reasoning
          </h1>
          <p className="max-w-2xl text-sm text-slate-600">
            By default you’re chatting with a fast GPT assistant. Toggle the
            Agent switch for a full multi-agent Intervention Mapping analysis—
            we’ll show you every step, then return to natural chat automatically.
          </p>
        </div>
        <AgentToggle enabled={agentEnabled} onChange={setAgentEnabled} />
      </header>

      <section className="grid gap-6 lg:grid-cols-3">
        <div className="flex flex-col gap-4 lg:col-span-2">
          <div className="h-[60vh] rounded-3xl border border-slate-200 bg-white/80 p-6 shadow-inner backdrop-blur">
            <div className="flex h-full flex-col gap-4 overflow-y-auto pr-2">
              {visibleMessages.map((message, index) => {
                const isUser = message.role === "user";
                return (
                  <div
                    key={`${message.role}-${index}-${message.content.slice(0, 12)}`}
                    className={`max-w-3xl rounded-2xl px-4 py-3 text-sm leading-relaxed shadow ${
                      isUser
                        ? "self-end bg-brand-600 text-white shadow-brand-500/40"
                        : "self-start bg-slate-50 text-slate-800"
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  </div>
                );
              })}
            </div>
          </div>
          {error && (
            <p className="text-sm text-rose-600">
              {error} Please try again or reload the page.
            </p>
          )}
          <ChatComposer onSend={handleSend} disabled={isSending} />
          <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">
            Mode: {agentEnabled ? "Agent workflow" : "ChatGPT-style conversation"}
          </p>
        </div>
        <AgentFlowVisualizer result={agentResult} runId={runId} />
      </section>
    </main>
  );
}

