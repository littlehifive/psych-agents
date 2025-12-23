"use client";

import { StoredConversation } from "@/lib/types";
import { Plus, MessageSquare } from "lucide-react";

interface SidebarProps {
    conversations: StoredConversation[];
    activeId?: string;
    onNewChat: () => void;
    onSelectChat: (id: string) => void;
}

export default function Sidebar({
    conversations,
    activeId,
    onNewChat,
    onSelectChat,
}: SidebarProps) {
    return (
        <aside className="flex h-screen w-72 flex-col border-r border-slate-200 bg-slate-50/50 backdrop-blur-xl">
            <div className="p-4">
                <button
                    onClick={onNewChat}
                    className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 shadow-sm transition-all hover:bg-slate-50 hover:shadow-md active:scale-[0.98]"
                >
                    <Plus className="h-5 w-5 text-brand-600" />
                    New Chat
                </button>
            </div>

            <div className="flex-1 overflow-y-auto px-3 pb-4">
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
                                                day: "numeric",
                                                hour: "2-digit",
                                                minute: "2-digit",
                                            })}
                                        </span>
                                    </div>
                                </button>
                            ))
                    )}
                </div>
            </div>

            <div className="mt-auto border-t border-slate-200 p-4">
                <div className="flex items-center gap-3 px-2">
                    <div className="h-8 w-8 rounded-full bg-gradient-to-br from-brand-600 to-brand-400 shadow-sm" />
                    <div className="flex flex-col">
                        <span className="text-sm font-semibold text-slate-700">Researcher</span>
                    </div>
                </div>
            </div>
        </aside>
    );
}
