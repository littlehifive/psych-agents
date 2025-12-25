"use client";

import { useMemo, useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { Bookmark, Check, Loader2 } from "lucide-react";
import ChatComposer from "@/components/chat-composer";
import Sidebar from "@/components/sidebar";
import LibraryView from "@/components/library-view";
import type { ChatMessage, StoredConversation, LibraryItem } from "@/lib/types";

const INITIAL_ASSISTANT_MESSAGE: ChatMessage = {
  role: "assistant",
  content:
    "Welcome to the Agentic Researcher Studio.\n\nI am designed to help NGO researchers apply agency-based theories to your intervention development work. Ask questions to explore concepts like agency, self-efficacy, and behavior change theories.\n\nHow can I assist you today?",
};

const STARTER_QUESTIONS = [
  "What is an agency-based intervention?",
  "What is a wise intervention?",
  "How do I design a health intervention to encourage skin-to-skin practice among mothers in rural India?"
];

export default function ConversationPage() {
  const [conversations, setConversations] = useState<StoredConversation[]>([]);
  const [activeId, setActiveId] = useState<string | undefined>(undefined);
  const [activeTab, setActiveTab] = useState<"chat" | "library">("chat");
  const [libraryItems, setLibraryItems] = useState<LibraryItem[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isMounted, setIsMounted] = useState(false);
  const [savingIds, setSavingIds] = useState<Record<number, boolean>>({});

  const activeConversation = useMemo(
    () => conversations.find((c) => c.id === activeId),
    [conversations, activeId]
  );

  const messages = useMemo(
    () => activeConversation?.messages || [INITIAL_ASSISTANT_MESSAGE],
    [activeConversation]
  );

  const visibleMessages = useMemo(
    () => messages.filter((message) => message.role !== "system"),
    [messages]
  );

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Persistence: Load from localStorage
  useEffect(() => {
    setIsMounted(true);
    const saved = localStorage.getItem("psych_agents_history");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setConversations(parsed);
        if (parsed.length > 0) {
          setActiveId(parsed[0].id);
        }
      } catch (e) {
        console.error("Failed to parse history", e);
      }
    }
    fetchLibrary();
  }, []);

  // Persistence: Save to localStorage
  useEffect(() => {
    if (isMounted) {
      localStorage.setItem("psych_agents_history", JSON.stringify(conversations));
    }
  }, [conversations, isMounted]);

  const fetchLibrary = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_COUNCIL_API || "http://localhost:8000"}/library`);
      if (response.ok) {
        const items = await response.json();
        setLibraryItems(items);
      }
    } catch (e) {
      console.error("Failed to fetch library", e);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (activeTab === "chat") {
      scrollToBottom();
    }
  }, [visibleMessages, activeTab]);

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsSending(false);
    }
  };

  const handleNewChat = () => {
    setActiveTab("chat");
    if (messages.length <= 1 && activeId) return;
    const newId = crypto.randomUUID();
    setActiveId(newId);
  };

  const handleSelectChat = (id: string) => {
    if (isSending) return;
    setActiveTab("chat");
    setActiveId(id);
  };

  const updateActiveConversation = (newMessages: ChatMessage[]) => {
    setConversations((prev) => {
      const existing = prev.find((c) => c.id === activeId);
      const now = Date.now();

      if (existing) {
        return prev.map((c) =>
          c.id === activeId ? { ...c, messages: newMessages, updatedAt: now } : c
        );
      } else {
        const firstUserMsg = newMessages.find(m => m.role === 'user')?.content || "New Chat";
        const title = firstUserMsg.length > 40 ? firstUserMsg.slice(0, 40) + "..." : firstUserMsg;

        const newConv: StoredConversation = {
          id: activeId || crypto.randomUUID(),
          title,
          messages: newMessages,
          updatedAt: now,
        };
        if (!activeId) setActiveId(newConv.id);
        return [newConv, ...prev];
      }
    });
  };

  const handleSaveToLibrary = async (index: number) => {
    const assistantMsg = messages[index];
    // Find the user prompt preceding this assistant message
    let userPrompt = "";
    for (let i = index - 1; i >= 0; i--) {
      if (messages[i].role === 'user') {
        userPrompt = messages[i].content;
        break;
      }
    }

    setSavingIds(prev => ({ ...prev, [index]: true }));

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_COUNCIL_API || "http://localhost:8000"}/library`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: userPrompt || "General Inquiry",
          answer: assistantMsg.content,
          citations: "" // Citations could be parsed from content if available
        })
      });

      if (!response.ok) throw new Error("Save failed");

      await fetchLibrary();
      // Show success state briefly
      setTimeout(() => {
        setSavingIds(prev => {
          const next = { ...prev };
          delete next[index];
          return next;
        });
      }, 2000);

    } catch (e) {
      console.error("Save failed", e);
      setSavingIds(prev => ({ ...prev, [index]: false }));
    }
  };

  const handleDeleteLibraryItem = async (id: string) => {
    try {
      await fetch(`${process.env.NEXT_PUBLIC_COUNCIL_API || "http://localhost:8000"}/library/${id}`, {
        method: "DELETE"
      });
      fetchLibrary();
    } catch (e) {
      console.error("Delete failed", e);
    }
  };

  const handleSend = async (content: string) => {
    let currentId = activeId;
    if (!currentId) {
      currentId = crypto.randomUUID();
      setActiveId(currentId);
    }

    const pendingMessages: ChatMessage[] = [...messages, { role: "user" as const, content }];

    const existing = conversations.find(c => c.id === currentId);
    if (!existing) {
      const title = content.length > 40 ? content.slice(0, 40) + "..." : content;
      setConversations(prev => [{
        id: currentId!,
        title,
        messages: pendingMessages,
        updatedAt: Date.now()
      }, ...prev]);
    } else {
      updateActiveConversation(pendingMessages);
    }

    setIsSending(true);
    setError(null);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_COUNCIL_API || "http://localhost:8000"}/conversation/send/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          messages: pendingMessages,
          session_id: currentId,
        }),
      });

      if (!response.ok) throw new Error("Chat stream failed");

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No reader");

      const decoder = new TextDecoder();
      let buffer = "";
      let currentAssistantMessage = "";

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

              setConversations(prev => prev.map(c =>
                c.id === currentId
                  ? { ...c, messages: [...pendingMessages, { role: "assistant", content: currentAssistantMessage }] }
                  : c
              ));
            }
          } else if (line.startsWith("event: complete")) {
            const dataLine = line.split("\n").find(l => l.startsWith("data: "));
            if (dataLine) {
              const data = JSON.parse(dataLine.slice(6));
              setConversations(prev => prev.map(c =>
                c.id === currentId
                  ? { ...c, messages: [...pendingMessages, { role: "assistant", content: data.message.content }], updatedAt: Date.now() }
                  : c
              ));
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name === 'AbortError') return;
      console.error(err);
      setError(err.message || "Unable to send message.");
    } finally {
      setIsSending(false);
      abortControllerRef.current = null;
    }
  };

  if (!isMounted) return null;

  return (
    <div className="flex h-screen bg-white">
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        activeTab={activeTab}
        onNewChat={handleNewChat}
        onSelectChat={handleSelectChat}
        onTabChange={setActiveTab}
      />

      <main className="flex flex-1 flex-col overflow-hidden">
        {activeTab === "library" ? (
          <LibraryView items={libraryItems} onDeleteItem={handleDeleteLibraryItem} />
        ) : (
          <div className="mx-auto flex h-full w-full max-w-5xl flex-col gap-8 px-6 py-10">
            <header className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
              <div className="flex flex-col gap-2">
                <p className="w-fit bg-gradient-to-r from-brand-600 to-brand-400 bg-clip-text text-sm font-bold uppercase tracking-[0.2em] text-transparent">
                  Agentic Researcher Studio
                </p>
                <h1 className="max-w-3xl text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl">
                  Design stronger interventions by putting{" "}
                  <span className="text-brand-600">agency at the center</span>
                </h1>
                <p className="max-w-4xl text-sm leading-relaxed text-slate-500 text-pretty">
                  Built for NGO researchers, <strong>Agentic Researcher Studio</strong> bridges
                  theory and practice. Chat to learn core concepts and save your favorite ideas to the library.
                </p>
              </div>
            </header>

            <div className="flex flex-1 flex-col gap-4 overflow-hidden">
              <div className="flex-1 rounded-3xl border border-slate-200 bg-white/80 p-6 shadow-inner backdrop-blur overflow-hidden">
                <div className="flex h-full flex-col gap-4 overflow-y-auto pr-2">
                  {visibleMessages.map((message, index) => {
                    const isUser = message.role === "user";
                    const actualIndex = messages.indexOf(message);
                    const isSaving = savingIds[actualIndex];
                    const isSaved = isSaving === false; // Using boolean false to indicate "just saved"

                    return (
                      <div
                        key={`${message.role}-${index}-${message.content.slice(0, 12)}`}
                        className={`group relative max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${isUser
                          ? "self-end bg-slate-200 text-slate-900"
                          : "self-start bg-slate-50 text-slate-800"
                          }`}
                      >
                        <div className="prose prose-sm max-w-none dark:prose-invert">
                          <ReactMarkdown>{message.content}</ReactMarkdown>
                        </div>

                        {!isUser && (
                          <button
                            onClick={() => handleSaveToLibrary(actualIndex)}
                            disabled={isSaving}
                            className={`absolute -right-12 top-2 p-2 rounded-full border transition-all ${isSaving
                              ? "bg-brand-50 border-brand-200 text-brand-600 cursor-wait"
                              : "bg-white border-slate-200 text-slate-400 hover:text-brand-600 hover:border-brand-200 opacity-0 group-hover:opacity-100 shadow-sm"
                              }`}
                            title="Save to Library"
                          >
                            {isSaving ? (
                              <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            ) : (
                              <Bookmark className="h-3.5 w-3.5" />
                            )}
                          </button>
                        )}
                      </div>
                    );
                  })}
                  {messages.length <= 1 && !isSending && (
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
              <ChatComposer onSend={handleSend} onStop={handleStop} disabled={isSending} />
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">
                  RAG-backed Theory Assistant
                </p>
                {activeConversation && (
                  <p className="text-[10px] text-slate-300">
                    Session: {activeId?.slice(0, 8)} | Updated: {new Date(activeConversation.updatedAt).toLocaleTimeString()}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
