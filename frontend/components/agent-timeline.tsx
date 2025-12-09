import type { AgentTrace } from "@/lib/types";

interface Props {
  traces: AgentTrace[];
  title?: string;
}

const timeFormatter = new Intl.DateTimeFormat("en-US", {
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
});

export function AgentTimeline({ traces, title = "Agent Timeline" }: Props) {
  if (!traces?.length) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-600">{title}</h3>
        <p className="text-sm text-slate-500">
          The Theory Council has not run yet for this session.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-600">{title}</h3>
      <ol className="mt-4 space-y-3">
        {traces.map((trace) => {
          const startTime = timeFormatter.format(new Date(trace.started_at));
          const duration = trace.duration_ms
            ? `${(trace.duration_ms / 1000).toFixed(1)}s`
            : "—";
          const category = trace.metadata?.category as string | undefined;

          return (
            <li
              key={`${trace.agent_key}-${trace.started_at}`}
              className="rounded-lg border border-slate-100 bg-slate-50/70 p-3"
            >
              <div className="flex items-center justify-between text-sm font-medium text-slate-700">
                <span>{trace.agent_label}</span>
                <span className="text-xs text-slate-500">{startTime}</span>
              </div>
              <div className="mt-1 text-xs uppercase tracking-wide text-slate-400">
                {category ?? "agent"}
              </div>
              <p className="mt-2 line-clamp-4 text-sm text-slate-600">
                {trace.output}
              </p>
              <div className="mt-2 text-xs text-slate-500">
                Duration: {duration}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

export default AgentTimeline;

