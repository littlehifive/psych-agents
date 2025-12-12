"use client";

import { useMemo, useState, useRef, useEffect } from "react";
import AgentToggle from "@/components/agent-toggle";
import ChatComposer from "@/components/chat-composer";
import AgentFlowVisualizer from "@/components/agent-flow-visualizer";
import { sendConversation } from "@/lib/api";
import type { ChatMessage, CouncilResult } from "@/lib/types";

const INITIAL_ASSISTANT_MESSAGE: ChatMessage = {
  role: "assistant",
  content:
    "Welcome to the Agentic Researcher Studio.\n\nI am designed to help NGO researchers apply agency-based theories to your intervention development work.\n\n• **Learning Mode (Agent Off)**: Ask questions to explore concepts like agency, self-efficacy, and behavior change theories.\n• **Council Mode (Agent On)**: Toggle the agent switch to convene a council of psychologists who will debate and design rigorous solutions for your specific problem.\n\nHow can I assist you today?",
};

const STARTER_QUESTIONS = [
  "What is agency-based intervention?",
  "Explain Self-Determination Theory",
  "How do I increase community ownership?",
  "Help me design a youth program"
];

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

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [visibleMessages]);

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

    // Standard chat flow (streaming)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_COUNCIL_API || "http://localhost:8000"}/conversation/send/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          messages: pendingMessages,
          agent_enabled: false,
          session_id: sessionId,
        }),
      });

      if (!response.ok) throw new Error("Chat stream failed");

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No reader");

      const decoder = new TextDecoder();
      let buffer = "";
      let currentAssistantMessage = "";

      // Add an empty assistant message to start filling
      setMessages(prev => [...prev, { role: "assistant", content: "" }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("event: token")) {
            const dataLine = line.split("\n").find(l => l.startsWith("data: "));
            if (dataLine) {
              const data = JSON.parse(dataLine.slice(6));
              currentAssistantMessage += data.chunk;
              setMessages(prev => {
                const msgs = [...prev];
                msgs[msgs.length - 1] = { role: "assistant", content: currentAssistantMessage };
                return msgs;
              });
            }
          } else if (line.startsWith("event: complete")) {
            const dataLine = line.split("\n").find(l => l.startsWith("data: "));
            if (dataLine) {
              const data = JSON.parse(dataLine.slice(6));
              setSessionId(data.session_id);
              // Finalize the message with exact server content
              setMessages(prev => {
                const msgs = [...prev];
                msgs[msgs.length - 1] = { role: "assistant", content: data.message.content };
                return msgs;
              });
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
        console.log("Chat aborted by user");
        messages.pop();
        return;
      }
      console.error(err);
      setError(err.message || "Unable to send message.");
      setMessages(prev => prev.filter(m => m.content !== ""));
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
            Agentic Researcher Studio
          </p>
          <h1 className="text-3xl font-bold text-slate-900">
            Design stronger interventions by putting agency at the center
          </h1>
          <p className="max-w-2xl text-sm text-slate-600">
            Built for NGO researchers, Agentic Researcher Studio bridges theory and practice, helping you explore agency-related theories, translate them into actionable designs, and tackle real-world problems. Chat to learn core concepts, or activate the Theory Council to convene expert perspectives for deep, structured intervention design.
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
              {messages.length === 1 && (
                <div className="mt-4 flex flex-wrap gap-2 px-1">
                  {STARTER_QUESTIONS.map((q) => (
                    <button
                      key={q}
                      onClick={() => handleSend(q)}
                      className="rounded-full border border-brand-100 bg-brand-50 px-3 py-1.5 text-xs font-medium text-brand-700 hover:bg-brand-100 hover:text-brand-800 transition-colors"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              )}
              <div ref={messagesEndRef} />
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

