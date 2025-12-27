"use client";

import { useMemo, useState } from "react";
import { StoredConversation } from "@/lib/types";
import { Plus, MessageSquare, BookOpen, MessageCircle, MoreVertical, Trash2 } from "lucide-react";

interface SidebarProps {
    conversations: StoredConversation[];
    activeId?: string;
    activeTab: "chat" | "library";
    onNewChat: () => void;
    onSelectChat: (id: string) => void;
    onTabChange: (tab: "chat" | "library") => void;
    onClearChats: () => void;
}

export default function Sidebar({
    conversations,
    activeId,
    activeTab,
    onNewChat,
    onSelectChat,
    onTabChange,
    onClearChats,
}: SidebarProps) {
    const [showSettings, setShowSettings] = useState(false);

    return (
        <aside className="flex h-screen w-72 flex-col border-r border-slate-200 bg-slate-50/50 backdrop-blur-xl">
            <div className="p-4 flex flex-col gap-4">
                <button
                    onClick={onNewChat}
                    className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 shadow-sm transition-all hover:bg-slate-50 hover:shadow-md active:scale-[0.98]"
                >
                    <Plus className="h-5 w-5 text-brand-600" />
                    New Chat
                </button>

                <div className="grid grid-cols-2 gap-1 p-1 bg-slate-100 rounded-xl border border-slate-200">
                    <button
                        onClick={() => onTabChange("chat")}
                        className={`flex items-center justify-center gap-2 py-2 text-xs font-bold rounded-lg transition-all ${activeTab === "chat"
                            ? "bg-white text-brand-600 shadow-sm"
                            : "text-slate-500 hover:text-slate-700"
                            }`}
                    >
                        <MessageCircle className="h-4 w-4" />
                        Chat
                    </button>
                    <button
                        onClick={() => onTabChange("library")}
                        className={`flex items-center justify-center gap-2 py-2 text-xs font-bold rounded-lg transition-all ${activeTab === "library"
                            ? "bg-white text-brand-600 shadow-sm"
                            : "text-slate-500 hover:text-slate-700"
                            }`}
                    >
                        <BookOpen className="h-4 w-4" />
                        Library
                    </button>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto px-3 pb-4">
                {activeTab === "chat" ? (
                    <>
                        <h2 className="mb-2 px-3 text-xs font-bold uppercase tracking-widest text-slate-400">
                            Recent Chats
                        </h2>
                        <div className="flex flex-col gap-1">
                            {conversations.length === 0 ? (
                                <p className="px-3 py-4 text-xs italic text-slate-400">
                                    No previous chats yet
                                </p>
                            ) : (
                                conversations
                                    .sort((a, b) => b.updatedAt - a.updatedAt)
                                    .map((conv) => (
                                        <button
                                            key={conv.id}
                                            onClick={() => onSelectChat(conv.id)}
                                            className={`group flex items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-all ${activeId === conv.id
                                                ? "bg-brand-50 text-brand-700 shadow-sm ring-1 ring-brand-200"
                                                : "text-slate-600 hover:bg-slate-100/80 hover:text-slate-900"
                                                }`}
                                        >
                                            <MessageSquare
                                                className={`h-4 w-4 shrink-0 ${activeId === conv.id ? "text-brand-600" : "text-slate-400 group-hover:text-slate-500"
                                                    }`}
                                            />
                                            <div className="flex flex-col overflow-hidden">
                                                <span className="truncate text-sm font-medium">
                                                    {conv.title || "Untitled Chat"}
                                                </span>
                                                <span className="text-[10px] text-slate-400">
                                                    {new Date(conv.updatedAt).toLocaleDateString([], {
                                                        month: "short",
                                                        day: "numeric"
                                                    })}
                                                </span>
                                            </div>
                                        </button>
                                    ))
                            )}
                        </div>
                    </>
                ) : (
                    <div className="px-3 py-4 flex flex-col gap-3">
                        <p className="text-[10px] uppercase font-bold text-slate-400 tracking-widest">Navigation</p>
                        <p className="text-xs text-slate-500 leading-relaxed italic">
                            Use the Library tab to browse intervention components you've saved from your chats.
                        </p>
                    </div>
                )}
            </div>

            <div className="mt-auto border-t border-slate-200 p-4 relative">
                {showSettings && (
                    <div className="absolute bottom-full left-4 mb-2 min-w-[200px] gap-1 rounded-xl border border-slate-200 bg-white p-1 shadow-xl animate-in fade-in slide-in-from-bottom-2">
                        <button
                            onClick={() => {
                                onClearChats();
                                setShowSettings(false);
                            }}
                            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-rose-600 transition-colors hover:bg-rose-50"
                        >
                            <Trash2 className="h-4 w-4" />
                            Clear all chats
                        </button>
                    </div>
                )}
                <button
                    onClick={() => setShowSettings(!showSettings)}
                    className="flex w-full items-center justify-between gap-3 rounded-xl px-2 py-2 transition-colors hover:bg-slate-100"
                >
                    <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-full bg-gradient-to-br from-brand-600 to-brand-400 shadow-sm" />
                        <div className="flex flex-col">
                            <span className="text-sm font-semibold text-slate-700">Researcher</span>
                        </div>
                    </div>
                    <MoreVertical className={`h-4 w-4 text-slate-400 transition-transform ${showSettings ? "rotate-90 text-brand-600" : ""}`} />
                </button>
            </div>
        </aside>
    );
}
