import React from "react";
import type { CouncilResult } from "@/lib/types";
import clsx from "clsx";

interface Props {
  result?: CouncilResult | null;
}

const SECTION_ORDER: Array<{ key: keyof CouncilResult["sections"]; label: string }> = [
  { key: "problem_framing", label: "1. Problem Framing" },
  { key: "theory_council_debate", label: "2. Theory Council Debate" },
  { key: "intervention_mapping_guide", label: "3. Intervention Mapping Guide" },
  {
    key: "recommended_intervention_concepts",
    label: "4. Recommended Intervention Concept(s)",
  },
];

export function FourSectionReport({ result }: Props) {
  if (!result) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white/60 p-8 text-center text-slate-500">
        <p>Run the Theory Council to populate the four-section report.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {SECTION_ORDER.map(({ key, label }) => (
        <section
          key={key}
          className={clsx(
            "rounded-2xl border border-slate-200 bg-white/90 p-5 shadow-sm",
            key === "problem_framing" && "border-brand-200",
          )}
        >
          <header className="mb-2 flex items-center justify-between">
            <h3 className="text-base font-semibold text-slate-800">{label}</h3>
          </header>
          <article className="prose prose-sm max-w-none text-slate-700">
            {result.sections[key] ? (
              result.sections[key]
                ?.split("\n")
                .map((line, idx) => <p key={`${key}-${idx}`}>{line}</p>)
            ) : (
              <p className="text-slate-400">No content yet.</p>
            )}
          </article>
        </section>
      ))}
    </div>
  );
}

export default FourSectionReport;
