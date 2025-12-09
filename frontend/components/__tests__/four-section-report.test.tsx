import { render, screen } from "@testing-library/react";
import FourSectionReport from "@/components/four-section-report";
import React from "react";
import type { CouncilResult } from "@/lib/types";

const mockResult: CouncilResult = {
  raw_problem: "Example",
  framed_problem: "Framed",
  im_summary: "Summary",
  theory_outputs: {},
  debate_summary: "Debate",
  theory_ranking: "Ranking",
  final_synthesis: "1. Problem Framing",
  sections: {
    problem_framing: "PF content",
    theory_council_debate: "Debate content",
    intervention_mapping_guide: "Guide content",
    recommended_intervention_concepts: "Concept content",
  },
  agent_traces: [],
};

describe("FourSectionReport", () => {
  it("renders all four section headings", () => {
    render(<FourSectionReport result={mockResult} />);
    expect(screen.getByText("1. Problem Framing")).toBeInTheDocument();
    expect(screen.getByText("2. Theory Council Debate")).toBeInTheDocument();
    expect(screen.getByText("3. Intervention Mapping Guide")).toBeInTheDocument();
    expect(
      screen.getByText("4. Recommended Intervention Concept(s)"),
    ).toBeInTheDocument();
  });

  it("shows placeholder when no result provided", () => {
    render(<FourSectionReport result={null} />);
    expect(
      screen.getByText(/run the theory council to populate/i),
    ).toBeInTheDocument();
  });
});

