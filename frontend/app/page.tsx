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

  // Keep track of the abort controller for the active request
  const [abortController, setAbortController] = useState<AbortController | null>(null);

  const visibleMessages = useMemo(
    () => messages.filter((message) => message.role !== "system"),
    [messages],
  );

  const handleStop = () => {
    if (abortController) {
      abortController.abort();
      setAbortController(null);
      setIsSending(false);
      // Optional: Add a system message saying "Stopped by user"?
    }
  };

  const handleSend = async (content: string) => {
    // 1. Optimistic update
    const pendingMessages: ChatMessage[] = [...messages, { role: "user" as const, content }];
    setMessages(pendingMessages);
    setIsSending(true);
    setError(null);

    // Create new abort controller
    const controller = new AbortController();
    setAbortController(controller);

    // If agent is enabled, use the streaming endpoint directly so we see progress
    if (agentEnabled) {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_COUNCIL_API || "http://localhost:8000"}/council/run/stream`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          signal: controller.signal,
          body: JSON.stringify({
            problem: content,
            session_id: sessionId,
            chat_history: messages, // Pass ALL previous messages as history
            metadata: {},
          }),
        });

        if (!response.ok) throw new Error("Stream failed");

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No reader");

        const decoder = new TextDecoder();
        let buffer = "";

        // Reset agent result for new run
        setAgentResult({
          raw_problem: content,
          theory_outputs: {},
          sections: {},
          agent_traces: []
        } as any);

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          const lines = buffer.split("\n\n");
          buffer = lines.pop() || ""; // Keep incomplete chunk

          for (const line of lines) {
            if (line.startsWith("event: trace")) {
              const dataLine = line.split("\n").find(l => l.startsWith("data: "));
              if (dataLine) {
                const data = JSON.parse(dataLine.slice(6));
                setAgentResult(prev => {
                  const existing = prev?.agent_traces || [];
                  return { ...prev!, agent_traces: [...existing, data.trace] };
                });
                if (data.run_id) setRunId(data.run_id);
              }
            } else if (line.startsWith("event: complete")) {
              const dataLine = line.split("\n").find(l => l.startsWith("data: "));
              if (dataLine) {
                const data = JSON.parse(dataLine.slice(6));
                setAgentResult(data.run.result);
                setRunId(data.run.run_id);
                setSessionId(data.run.session_id);
                setMessages(prev => [...prev, { role: "assistant", content: data.run.result.final_synthesis }]);
                setAgentEnabled(false);
              }
            } else if (line.startsWith("event: started")) {
              const dataLine = line.split("\n").find(l => l.startsWith("data: "));
              if (dataLine) {
                const data = JSON.parse(dataLine.slice(6));
                setSessionId(data.session_id);
              }
            }
          }
        }

      } catch (err: any) {
        if (err.name === 'AbortError') {
          console.log("Stream aborted by user");
          return; // Clean exit
        }
        console.error(err);
        setError("Streaming failed. Please check the backend.");
      } finally {
        setIsSending(false);
        setAbortController(null);
      }
      return;
    }

    // Standard chat flow (non-streaming or legacy)
    try {
      const response = await sendConversation({
        messages: pendingMessages,
        agent_enabled: agentEnabled,
        session_id: sessionId,
      });
      setSessionId(response.session_id);
      setMessages(response.messages);

      // Basic chat doesn't support aborting via API client wrapper easily unless we refactor api.ts
      // But user specifically asked for stopping the *agentic process*.

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
      setAbortController(null);
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
                    className={`max-w-3xl rounded-2xl px-4 py-3 text-sm leading-relaxed shadow ${isUser
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
          <ChatComposer onSend={handleSend} onStop={handleStop} disabled={isSending}>
            <AgentToggle enabled={agentEnabled} onChange={setAgentEnabled} />
          </ChatComposer>
          <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">
            Mode: {agentEnabled ? "Agent workflow" : "ChatGPT-style conversation"}
          </p>
        </div>
        <AgentFlowVisualizer result={agentResult} runId={runId} isLoading={isSending} />
      </section>
    </main>
  );
}

