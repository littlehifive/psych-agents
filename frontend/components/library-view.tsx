"use client";

import { useState, useMemo } from "react";
import { LibraryItem } from "@/lib/types";
import {
    Search,
    Filter,
    ChevronDown,
    ChevronRight,
    Tag,
    Clock,
    BookOpen,
    Trash2
} from "lucide-react";
import ReactMarkdown from "react-markdown";

interface LibraryViewProps {
    items: LibraryItem[];
    onDeleteItem?: (id: string) => void;
}

const THEMES = ["All", "SCT", "SDT", "Wise Interventions", "Intervention Mapping", "Other"];

export default function LibraryView({ items, onDeleteItem }: LibraryViewProps) {
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedTheme, setSelectedTheme] = useState("All");
    const [expandedId, setExpandedId] = useState<string | null>(null);

    const filteredItems = useMemo(() => {
        return items.filter((item) => {
            const matchesSearch =
                item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                item.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
                item.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()));

            const matchesTheme = selectedTheme === "All" || item.theme === selectedTheme;

            return matchesSearch && matchesTheme;
        });
    }, [items, searchQuery, selectedTheme]);

    const groupedItems = useMemo(() => {
        const groups: Record<string, LibraryItem[]> = {};
        filteredItems.forEach(item => {
            if (!groups[item.theme]) groups[item.theme] = [];
            groups[item.theme].push(item);
        });
        return groups;
    }, [filteredItems]);

    return (
        <div className="flex flex-col gap-6 h-full p-6 bg-slate-50/30 overflow-hidden">
            <div className="flex flex-col gap-4">
                <h2 className="text-2xl font-bold text-slate-900">Intervention Library</h2>

                <div className="flex items-center gap-4">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                        <input
                            type="text"
                            placeholder="Search by title, summary, or tags..."
                            className="w-full pl-10 pr-4 py-2 rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all text-sm"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>

                    <div className="flex items-center gap-2">
                        <Filter className="h-4 w-4 text-slate-400" />
                        <select
                            className="bg-white border border-slate-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                            value={selectedTheme}
                            onChange={(e) => setSelectedTheme(e.target.value)}
                        >
                            {THEMES.map(t => (
                                <option key={t} value={t}>{t}</option>
                            ))}
                        </select>
                    </div>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto pr-2 flex flex-col gap-8 pb-10">
                {Object.entries(groupedItems).length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-64 text-slate-400 gap-3">
                        <BookOpen className="h-10 w-10 opacity-20" />
                        <p className="text-sm">No saved items found matching your filters.</p>
                    </div>
                ) : (
                    Object.entries(groupedItems)
                        .sort(([a], [b]) => a.localeCompare(b))
                        .map(([theme, themeItems]) => (
                            <section key={theme} className="flex flex-col gap-4">
                                <div className="flex items-center gap-3">
                                    <div className="h-px flex-1 bg-slate-200" />
                                    <span className="text-xs font-bold uppercase tracking-widest text-slate-400 px-2 py-1 bg-white rounded-lg border border-slate-100 italic">
                                        {theme}
                                    </span>
                                    <div className="h-px flex-1 bg-slate-200" />
                                </div>

                                <div className="grid gap-4">
                                    {themeItems.map((item) => (
                                        <div
                                            key={item.id}
                                            className={`group rounded-2xl border border-slate-200 bg-white shadow-sm transition-all hover:shadow-md ${expandedId === item.id ? 'ring-2 ring-brand-500/20 border-brand-500' : ''}`}
                                        >
                                            <div
                                                className="p-4 cursor-pointer flex items-start gap-4"
                                                onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
                                            >
                                                <div className="mt-1">
                                                    {expandedId === item.id ? <ChevronDown className="h-5 w-5 text-brand-600" /> : <ChevronRight className="h-5 w-5 text-slate-400" />}
                                                </div>

                                                <div className="flex-1 flex flex-col gap-1">
                                                    <div className="flex items-baseline justify-between">
                                                        <h3 className="font-bold text-slate-900 group-hover:text-brand-600 transition-colors">
                                                            {item.title}
                                                        </h3>
                                                        <div className="flex items-center gap-2">
                                                            <span className="flex items-center gap-1 text-[10px] font-medium text-slate-400">
                                                                <Clock className="h-3 w-3" />
                                                                {new Date(item.createdAt).toLocaleDateString()}
                                                            </span>
                                                            {onDeleteItem && (
                                                                <button
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        onDeleteItem(item.id);
                                                                    }}
                                                                    className="p-1.5 opacity-0 group-hover:opacity-100 hover:bg-rose-50 hover:text-rose-600 rounded-md transition-all"
                                                                >
                                                                    <Trash2 className="h-3.5 w-3.5" />
                                                                </button>
                                                            )}
                                                        </div>
                                                    </div>

                                                    <p className="text-sm text-slate-600 leading-relaxed italic">
                                                        {item.summary}
                                                    </p>

                                                    <div className="flex flex-wrap gap-2 mt-2">
                                                        {item.tags.map(tag => (
                                                            <span key={tag} className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-100 text-[10px] font-bold text-slate-500 uppercase tracking-tighter">
                                                                <Tag className="h-2 w-2" />
                                                                {tag}
                                                            </span>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>

                                            {expandedId === item.id && (
                                                <div className="px-12 pb-6 pt-2 border-t border-slate-100 bg-slate-50/50 rounded-b-2xl">
                                                    <div className="flex flex-col gap-6">
                                                        <div className="flex flex-col gap-2">
                                                            <h4 className="text-xs font-bold uppercase text-slate-400 tracking-wider">Research Question</h4>
                                                            <p className="text-sm font-medium text-slate-800 bg-white p-3 rounded-xl border border-slate-200">
                                                                {item.question}
                                                            </p>
                                                        </div>

                                                        <div className="flex flex-col gap-2">
                                                            <h4 className="text-xs font-bold uppercase text-slate-400 tracking-wider">Intervention Guidance</h4>
                                                            <div className="prose prose-sm max-w-none text-slate-700 bg-white p-4 rounded-xl border border-slate-200">
                                                                <ReactMarkdown>{item.answer}</ReactMarkdown>
                                                            </div>
                                                        </div>

                                                        {item.citations && (
                                                            <div className="flex flex-col gap-2">
                                                                <h4 className="text-xs font-bold uppercase text-slate-400 tracking-wider">Citations</h4>
                                                                <p className="text-xs text-slate-500 italic bg-slate-100/50 p-2 rounded-lg">
                                                                    {item.citations}
                                                                </p>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </section>
                        ))
                )}
            </div>
        </div>
    );
}
