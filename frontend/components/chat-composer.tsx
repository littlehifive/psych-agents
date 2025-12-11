"use client";

import { useState } from "react";

interface Props {
  onSend: (message: string) => Promise<void> | void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatComposer({ onSend, disabled, placeholder }: Props) {
  const [message, setMessage] = useState("");
  const [isSending, setIsSending] = useState(false);

  const handleSend = async () => {
    const trimmed = message.trim();
    if (!trimmed) return;
    setIsSending(true);
    try {
      await onSend(trimmed);
      setMessage("");
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white/95 p-4 shadow-sm backdrop-blur">
      <textarea
        className="w-full resize-none rounded-xl border border-slate-200 bg-white/80 p-3 text-sm text-slate-800 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-200"
        rows={4}
        placeholder={
          placeholder ||
          "Ask a follow-up question, describe a constraint, or request a new plan..."
        }
        value={message}
        disabled={disabled || isSending}
        onChange={(event) => setMessage(event.target.value)}
        onKeyDown={(e) => {
          if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
            e.preventDefault();
            handleSend();
          }
        }}
      />
      <div className="mt-3 flex items-center justify-between text-sm text-slate-600">
        <span className="text-xs text-slate-400 hidden lg:inline-block">
          Press <kbd className="font-sans">Cmd+Enter</kbd> to send
        </span>
        <button
          type="button"
          onClick={handleSend}
          disabled={disabled || isSending || !message.trim()}
          className="rounded-full bg-brand-600 px-5 py-2 text-sm font-semibold text-white shadow-lg shadow-brand-600/30 transition hover:bg-brand-500 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {isSending ? "Thinking..." : "Send"}
        </button>
      </div>
    </div>
  );
}

export default ChatComposer;

