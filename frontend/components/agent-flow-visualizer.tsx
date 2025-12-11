import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Users,
  BrainCircuit,
  MessageSquare,
  FileText,
  CheckCircle,
  Loader2,
  GitGraph,
  Scale
} from "lucide-react";
import type { CouncilResult } from "@/lib/types";
import AgentTimeline from "./agent-timeline";
import FourSectionReport from "./four-section-report";

interface Props {
  result: CouncilResult | null;
  runId?: string | null;
  isLoading?: boolean;
}

const AGENT_ICONS: Record<string, any> = {
  problem_framer: FileText,
  im_anchor: GitGraph,
  sct: Users,
  sct_agent: Users,
  sdt: Users,
  sdt_agent: Users,
  wise: Users,
  wise_agent: Users,
  ra: Users,
  ra_agent: Users,
  env_impl: Users,
  env_impl_agent: Users,
  debate_moderator: MessageSquare,
  theory_selector: Scale,
  integrator: BrainCircuit,
};

const AGENT_COLORS: Record<string, string> = {
  problem_framer: "text-blue-500 bg-blue-50 border-blue-200",
  im_anchor: "text-purple-500 bg-purple-50 border-purple-200",
  sct_agent: "text-emerald-500 bg-emerald-50 border-emerald-200",
  sdt_agent: "text-emerald-500 bg-emerald-50 border-emerald-200",
  wise_agent: "text-emerald-500 bg-emerald-50 border-emerald-200",
  ra_agent: "text-emerald-500 bg-emerald-50 border-emerald-200",
  env_impl_agent: "text-emerald-500 bg-emerald-50 border-emerald-200",
  debate_moderator: "text-orange-500 bg-orange-50 border-orange-200",
  theory_selector: "text-pink-500 bg-pink-50 border-pink-200",
  integrator: "text-indigo-500 bg-indigo-50 border-indigo-200",
};

export function AgentFlowVisualizer({ result, runId, isLoading }: Props) {
  const [selectedTrace, setSelectedTrace] = useState<any | null>(null);

  // We rely on the parent (page.tsx) to stream items into result.agent_traces in real-time.
  // So we don't need internal replay logic anymore, OR we keep it only if we're not loading?
  // Current implementation in page.tsx appends traces live.
  // So `result.agent_traces` will grow.

  if (isLoading && result?.agent_traces?.length === 0) {
    // Initial loading before first trace
    return (
      <div className="rounded-2xl border border-brand-100 bg-white p-8 text-center shadow-lg">
        <div className="flex flex-col items-center gap-4">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          >
            <Loader2 className="h-10 w-10 text-brand-500" />
          </motion.div>
          <div>
            <h3 className="text-lg font-semibold text-slate-800">The Council is Convening</h3>
            <p className="text-sm text-slate-500">Orchestrating agents...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white/70 p-6 text-center text-slate-500">
        <p>Enable the Agent toggle to orchestrate the full Theory Council.</p>
      </div>
    );
  }

  const traces = result.agent_traces ?? [];
  const visibleTraces = traces; // All traces are visible now

  return (
    <div className="space-y-6">
      <div className="relative rounded-2xl border border-brand-100 bg-slate-50/50 p-6">
        <h3 className="mb-4 text-xs font-bold uppercase tracking-widest text-slate-500">
          Agent Execution Flow
        </h3>

        <div className="relative space-y-4 before:absolute before:inset-y-0 before:left-[27px] before:w-0.5 before:bg-slate-200 before:content-['']">
          <AnimatePresence>
            {traces.map((trace, index) => {
              const Icon = AGENT_ICONS[trace.agent_key] || CheckCircle;
              const colorClass = AGENT_COLORS[trace.agent_key] || "text-slate-500 bg-slate-50 border-slate-200";
              const isLast = index === traces.length - 1;

              return (
                <motion.div
                  key={`${runId}-${trace.agent_key}-${index}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ type: "spring", stiffness: 300, damping: 24 }}
                  className="relative flex gap-4"
                >
                  <div className={`relative z-10 flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border bg-white shadow-sm ${colorClass}`}>
                    <Icon className="h-6 w-6" />
                    {isLast && isLoading && (
                      <span className="absolute -right-1 -top-1 flex h-3 w-3">
                        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-400 opacity-75"></span>
                        <span className="relative inline-flex h-3 w-3 rounded-full bg-brand-500"></span>
                      </span>
                    )}
                  </div>

                  <div
                    className="flex-1 cursor-pointer rounded-xl border border-slate-200 bg-white p-3 shadow-sm transition hover:border-brand-300 hover:shadow-md"
                    onClick={() => setSelectedTrace(trace)}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-800">{trace.agent_label}</span>
                      <span className="text-[10px] uppercase text-slate-400">{trace.metadata?.category}</span>
                    </div>
                    <p className="mt-1 line-clamp-2 text-xs text-slate-600">
                      {trace.output}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: !isLoading && result.final_synthesis ? 1 : 0 }}
        transition={{ delay: 0.5 }}
      >
        <FourSectionReport result={result} />
      </motion.div>

      <AgentTimeline traces={traces} title="Execution Timestamps" />

      {/* Detail Modal */}
      <AnimatePresence>
        {selectedTrace && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4" onClick={() => setSelectedTrace(null)}>
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              onClick={(e) => e.stopPropagation()}
              className="relative max-h-[80vh] w-full max-w-2xl overflow-hidden rounded-2xl bg-white shadow-2xl"
            >
              <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
                <div>
                  <h3 className="text-lg font-bold text-slate-900">{selectedTrace.agent_label}</h3>
                  <p className="text-xs text-slate-500 uppercase tracking-widest">{selectedTrace.metadata?.category}</p>
                </div>
                <button
                  onClick={() => setSelectedTrace(null)}
                  className="rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                >
                  ✕
                </button>
              </div>
              <div className="overflow-y-auto p-6 text-sm text-slate-700 leading-relaxed whitespace-pre-wrap max-h-[60vh]">
                {String(selectedTrace.output)}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default AgentFlowVisualizer;

