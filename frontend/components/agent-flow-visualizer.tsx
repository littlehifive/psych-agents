import { useEffect, useState } from "react";
import type { CouncilResult } from "@/lib/types";
import AgentTimeline from "./agent-timeline";
import FourSectionReport from "./four-section-report";

interface Props {
  result: CouncilResult | null;
  runId?: string | null;
}

export function AgentFlowVisualizer({ result, runId }: Props) {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    if (!result?.agent_traces.length) {
      setActiveIndex(0);
      return;
    }
    setActiveIndex(0);
    const id = setInterval(() => {
      setActiveIndex((prev) => {
        if (!result.agent_traces) return prev;
        if (prev >= result.agent_traces.length - 1) {
          clearInterval(id);
          return prev;
        }
        return prev + 1;
      });
    }, 900);
    return () => clearInterval(id);
  }, [runId, result]);

  if (!result) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white/70 p-6 text-center text-slate-500">
        <p>Enable the Agent toggle to orchestrate the full Theory Council.</p>
      </div>
    );
  }

  const traces = result.agent_traces ?? [];

  return (
    <div className="space-y-5">
      <div className="rounded-2xl border border-brand-100 bg-gradient-to-br from-brand-50 to-white p-5 shadow-sm">
        <p className="text-xs uppercase tracking-widest text-brand-500">
          Theory Council Workflow
        </p>
        <h3 className="text-lg font-semibold text-slate-900">
          Animated Agent Timeline
        </h3>
        <p className="mt-1 text-sm text-slate-600">
          Follow the Intervention Mapping anchor, theory agents, debate, and
          integrator as they synthesize your brief.
        </p>
        <ol className="mt-4 space-y-3">
          {traces.map((trace, index) => {
            const isActive = index === activeIndex;
            return (
              <li
                key={`${trace.agent_key}-${trace.started_at}`}
                className={`rounded-xl border p-3 text-sm transition ${
                  isActive
                    ? "border-brand-400 bg-white shadow-md shadow-brand-200/50"
                    : "border-slate-200 bg-white/80"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-800">
                    {trace.agent_label}
                  </span>
                  <span className="text-xs text-slate-500">
                    {trace.metadata?.category}
                  </span>
                </div>
                <p className="mt-1 line-clamp-3 text-slate-600">
                  {trace.output}
                </p>
              </li>
            );
          })}
        </ol>
      </div>
      <FourSectionReport result={result} />
      <AgentTimeline traces={traces} title="Agent timestamps" />
    </div>
  );
}

export default AgentFlowVisualizer;




