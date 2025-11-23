# AGENTS.md — Instructions for the Coding Assistant (v2)

You are an AI coding assistant helping evolve a LOCAL Python demo of a multi-agent **“Theory Council”** using **LangGraph + LangChain + OpenAI**.

The user already has a working v1–v1.5 with:

- A `theory_council` package.
- A LangGraph pipeline with:
  - `problem_framer`
  - IM anchor agent
  - Multiple theory agents (SCT, SDT, Wise, Reasoned Action, Environment & Implementation)
  - Debate Moderator
  - Theory Selector
  - Integrator
- A CLI that prints out problem framing, agent outputs, and a synthesis.

Your job is to **refine and simplify** the system’s behavior and outputs to serve a very specific purpose:

> **Help users develop relevant, theory-informed health promotion interventions for a problem**,  
> using:
> - a brief **AI framing** of the problem,
> - a **debate** between theory agents,
> - a concise **Intervention Mapping (IM) guide** based on prioritized theories, and
> - **actual intervention recommendations** grounded in those IM steps.

The multi-agent debate is there to deepen reasoning; the Intervention Mapping structure is there to make that depth **actionable**.

---

## 0. Keep and reuse the existing project structure

Assume the repo already looks like this:

```text
theory-council/
  .gitignore
  .env.example
  pyproject.toml OR requirements.txt
  README.md

  src/
    __init__.py
    theory_council/
      __init__.py
      config.py
      personas.py
      graph.py
      cli.py
````

**Do NOT** rebuild from scratch.

* Keep `config.py` and `.env` handling as is.
* Keep the overall graph architecture (problem_framer → IM anchor → theory agents → debate → theory selector → integrator).
* You may refactor node functions and prompts to:

  * shorten outputs,
  * enforce structure,
  * and align with the new 4-section format.

---

## 1. Global design changes

### 1.1. Final output: exactly four sections

The **Integrator** must now produce outputs in **four clear sections**, in this order:

1. **Problem Framing**

   * Show:

     * the user’s **raw problem** description, and
     * a concise AI-framed version of the problem that is passed to agents.

2. **Theory Council Debate**

   * A **short debate summary** between theory agents:

     * what each lens contributes,
     * where lenses disagree or have different emphases,
     * 2–3 promising combinations.

3. **Intervention Mapping Guide (IM-Oriented)**

   * A concise, high-level IM guide to structure the intervention:

     * Logic model highlights (who, what behavior, which environment).
     * Key outcomes and determinants to target.
     * A minimal number of IM-style change objectives and methods (no exhaustive matrices).

4. **Recommended Intervention Concept(s)**

   * 1–3 concrete **intervention concepts** (brief proposals) grounded in:

     * the **prioritized theories** (from the Theory Selector),
     * and the **IM guide** above.

Everything in the pipeline (IM anchor, theory agents, debate moderator, theory selector) exists to support these four sections.

**IMPORTANT:** Outputs should be **concise**:

* Aim for:

  * Section 1: ~2 short paragraphs.
  * Section 2: ~4–8 bullet points total.
  * Section 3: ~3–6 bullet points plus ~1 short paragraph if needed.
  * Section 4: 1–3 brief intervention concept descriptions (1 paragraph + 3–5 bullets each at most).

Avoid long essays and nested sub-sections.

### 1.2. Intervention Mapping: used but not over-elaborated

* Use **Intervention Mapping (IM)** as a backbone, but keep it light:

  * Step 1: a short **logic model of the problem**.
  * Step 2: a **small set** of priority behavioral & environmental outcomes and determinants.
  * Step 3: a **small set** of methods & applications.

No need to list full matrices or all steps 4–6. Only the amount that directly supports Section 3 and Section 4.

---

## 2. Personas: adjust for brevity and the 4-section goal

All personas live in `src/theory_council/personas.py`. Adjust existing constants and add new ones as needed.

### 2.1. IM Anchor persona — shorter, more focused

Update the IM anchor’s system prompt so it produces a **compact** summary that the Integrator can later reuse in Section 3, and that theory agents can read.

**Key behaviors:**

* Given the framed problem, output:

  * A **short logic model** (2–3 bullet clusters), not a full treatise.
  * A **short list** of:

    * 2–3 key behavioral outcomes.
    * 2–3 environmental outcomes.
    * 3–6 key determinants worth targeting.
* Identify **what kind of help** the user seems to need (mostly Step 2–3, but do this in one short bullet list).

Example (structure, not verbatim):

```python
IM_ANCHOR_SYSTEM_PROMPT = """
You are the Intervention Mapping (IM) Anchor Agent.

Your output must be SHORT and STRUCTURED. Target ~300–400 words max.

Given a structured description of a health promotion problem, you will:

1) Provide a compact LOGIC MODEL OF THE PROBLEM:
   - 2–3 bullet points on:
     • Priority population & setting
     • Main health problem & behaviors
     • Key environmental conditions and actors

2) Suggest a small LOGIC MODEL OF CHANGE:
   - 2–3 priority BEHAVIORAL outcomes
   - 2–3 priority ENVIRONMENTAL outcomes
   - 3–6 key DETERMINANTS (mix of individual + environment)

3) Briefly say which IM steps are most relevant for the user’s query (1–2 bullets).

Use simple bullet points. Avoid long paragraphs, tables, or exhaustive matrices.
"""
```

### 2.2. Theory agents — emphasize brevity and IM linkage

You already have persona prompts for:

* SCT (Social Cognitive Theory).
* SDT (Self-Determination Theory).
* Wise/Belonging.
* Reasoned Action / decision.
* Environment & Implementation.

Update each to:

* Remind them:

  * “Your answer should be concise (aim for ~300–400 words).”
  * “Use bullet lists and short paragraphs.”
* Instruct them to:

  * Focus on **only a few determinants** (3–6).
  * Propose **only a few methods and applications** that are most relevant.
  * Explicitly mention how their suggestions fit into **Intervention Mapping** (e.g., as determinants, methods, or applications).
* Avoid duplicating full IM structure; they should feed **ingredients** into the Integrator, not produce their own final IM sections.

Example (SCT agent structure):

```python
SCT_AGENT_SYSTEM_PROMPT = """
You are the Social Cognitive Theory (SCT) Agent, inspired by Albert Bandura's work.
You are NOT Albert Bandura and you do not speak as him.

Your answer must be concise (~300–400 words), mostly bullets.

You receive:
- A structured problem description
- An IM anchor summary (logic model and determinants)

Your job:
1) Identify 3–6 key SCT determinants to prioritize (e.g., self-efficacy, outcome expectations, observational learning, self-regulation, environmental facilitators/barriers).
2) For each determinant, propose 1–2 SCT-consistent CHANGE METHODS that fit IM Step 3 (e.g., modeling, guided practice, feedback).
3) For each method, suggest 1 concrete PRACTICAL APPLICATION suited to the context (e.g., WhatsApp message sequence, group role-plays, brief scripts for nurses).

Format:
- Short bullets grouped by determinant.
- A final 2–3 bullet “Notes” section on risks or boundary conditions.

Do NOT produce full IM sections or long narratives; you are feeding ingredients to the Theory Council, not writing the final plan.
"""
```

Apply analogous changes to the SDT, Wise, RA, and Environment & Implementation agents.

### 2.3. Debate Moderator persona — keep as is but limit length

The Debate Moderator already summarizes complementarities and tensions. Now:

* Enforce that it must be short (~300–400 words).
* Ask it to produce mainly **bullets**, with a maximum of:

  * 6–10 bullets total.
  * It should clearly highlight:

    * What each lens adds.
    * Any noteworthy tensions.
    * 2–3 promising combinations for this problem.

Example addition to its system prompt:

```python
DEBATE_MODERATOR_SYSTEM_PROMPT = """
You are the Debate Moderator for the Theory Council.

Your job is to produce a SHORT summary (~300–400 words) in bullet form.

...
Limit yourself to:
- At most 2 bullets per theory on what it contributes.
- 2–3 bullets on main tensions.
- 2–3 bullets on promising theory combinations.

Avoid long paragraphs. Your output will be shown directly to the user as the 'Theory Council Debate' section.
"""
```

### 2.4. Theory Selector persona — more concise decision note

The Theory Selector’s job stays the same conceptually, but:

* Its ranking and rationale will mostly inform the Integrator.
* Its output should be short enough that if printed, it doesn’t take more than ~300–400 words.
* Ask it for a **ranked list + 1 short “decision note” paragraph**.

Example modification:

```python
THEORY_SELECTOR_SYSTEM_PROMPT = """
You are the Theory Selector (Decision Agent) for the Theory Council.

Your output must be concise (~300–400 words).

Tasks:
1) Rank the theories for THIS problem (SCT, SDT, Wise, Reasoned Action, Environment & Implementation):
   - Use a numbered list with a short (1–2 sentence) rationale for each.

2) Recommend the TOP 1–3 lenses (or combinations) for designing the intervention.

3) Provide a short 'Decision Note' paragraph explaining:
   - Why these lenses are best suited,
   - How they align with the IM anchor’s determinants and context.

Keep everything brief. Avoid repeating full details from the theory outputs.
"""
```

### 2.5. Integrator persona — enforce the four sections

The Integrator is the key piece to change.

Update `INTEGRATOR_SYSTEM_PROMPT` so that it:

* Always produces **four sections**, numbered and titled as:

  1. **Problem Framing**
  2. **Theory Council Debate**
  3. **Intervention Mapping Guide**
  4. **Recommended Intervention Concept(s)**

* Uses:

  * `raw_problem`
  * `framed_problem`
  * `im_summary`
  * `theory_outputs`
  * `debate_summary`
  * `theory_ranking` (decision note)

* Stays within ~800–1200 words total (as a soft guideline).

Example:

```python
INTEGRATOR_SYSTEM_PROMPT = """
You are the Integrator Agent for a 'Theory Council' of psychological intervention designers.

You receive:
- The user's RAW PROBLEM description.
- A FRAMED PROBLEM description.
- An IM anchor summary (logic model and determinants).
- Outputs from multiple theory agents (SCT, SDT, Wise, Reasoned Action, Environment & Implementation).
- A Debate Moderator summary.
- A Theory Selector ranking and decision note.

Your job is to produce a SINGLE, CONCISE output organized into EXACTLY FOUR SECTIONS:

1. Problem Framing
   - Show the raw problem text (quoted or paraphrased once).
   - Provide a short, clear AI framing in your own words (2–4 sentences).
   - This framing should be similar to what was given to the agents.

2. Theory Council Debate
   - Summarize the main points from the debate moderator and the theory selector:
     • What each key theory lens brings.
     • Main tensions or trade-offs.
     • 2–3 promising combinations.
   - Use bullets. Keep this brief (~6–10 bullets total).

3. Intervention Mapping Guide
   - Provide a compact IM-oriented guide, based on the prioritized theories:
     • 2–3 priority BEHAVIORAL outcomes.
     • 2–3 priority ENVIRONMENTAL outcomes.
     • 3–6 key DETERMINANTS to target, labeled with which theories support them.
     • 3–6 IM-style CHANGE METHODS (at a high level) that follow from those determinants.
   - Use bullets and short phrases. This is a guide, not a full IM workbook.

4. Recommended Intervention Concept(s)
   - Propose 1–3 concrete intervention concepts (e.g., "WhatsApp KMC coaching with norms & self-efficacy support", "Nurse-led group debrief with autonomy-supportive scripts").
   - For EACH concept, provide:
     • A 2–4 sentence description (who, what, where, via which channel).
     • 3–5 bullets linking it back to:
         – the prioritized theories,
         – the determinants and methods from Section 3.
   - These concepts should be realistic starting points for a health promotion team using Intervention Mapping.

GENERAL RULES:
- Be concise. Avoid repeating long passages from earlier agents.
- Use clear headings "1. Problem Framing", "2. Theory Council Debate", etc.
- Do NOT introduce new theories. Only build from the existing theory-agent outputs and IM anchor.
"""
```

---

## 3. graph.py — state and flow remain similar, but Integrator uses new structure

In `src/theory_council/graph.py`:

* You likely already have a `CouncilState` similar to:

  ```python
  class CouncilState(TypedDict):
      raw_problem: str
      framed_problem: str
      im_summary: Optional[str]
      theory_outputs: Dict[str, str]
      debate_summary: Optional[str]
      theory_ranking: Optional[str]
      final_synthesis: Optional[str]
  ```

* Keep this structure.

* Ensure the Integrator node has access to the **raw problem** as well as `framed_problem` and other fields.

  * If the Integrator node doesn’t have the raw problem yet, adjust the node to take it from `state["raw_problem"]` and include it in the user message.

Example Integrator node skeleton (logic only):

```python
def integrator(state: CouncilState) -> CouncilState:
    llm = get_llm(temperature=0.4)
    theory_outputs = state.get("theory_outputs") or {}
    # Serialize theory outputs if needed (shortened)
    combined_theories = []
    for key, label in [
        ("sct", "SCT (Social Cognitive Theory)"),
        ("sdt", "SDT (Self-Determination Theory)"),
        ("wise", "Wise / Belonging"),
        ("ra", "Reasoned Action / Decision"),
        ("env_impl", "Environment & Implementation"),
    ]:
        if key in theory_outputs:
            combined_theories.append(f"=== {label} ({key}) ===\n{theory_outputs[key]}")
    theories_text = "\n\n".join(combined_theories)

    user_content = (
        "RAW PROBLEM:\n"
        + state["raw_problem"]
        + "\n\nFRAMED PROBLEM:\n"
        + state["framed_problem"]
        + "\n\nIM ANCHOR SUMMARY:\n"
        + (state.get("im_summary") or "")
        + "\n\nTHEORY AGENT OUTPUTS:\n"
        + theories_text
        + "\n\nDEBATE SUMMARY:\n"
        + (state.get("debate_summary") or "")
        + "\n\nTHEORY RANKING AND DECISION NOTE:\n"
        + (state.get("theory_ranking") or "")
    )

    messages = [
        {"role": "system", "content": INTEGRATOR_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    resp = llm.invoke(messages)
    new_state = dict(state)
    new_state["final_synthesis"] = resp.content
    return new_state
```

The wiring of the graph (nodes and edges) can remain as in the previous version:

* `problem_framer` → `im_anchor` → theory agents → `debate_moderator` → `theory_selector` → `integrator`.

---

## 4. cli.py — print the four sections clearly

In `src/theory_council/cli.py`:

* The Integrator now returns a single `final_synthesis` already structured into the four sections.
* Simplify the CLI output to:

  * Option A: print only `final_synthesis` (since it includes all four sections).
  * Option B: optionally print some intermediate state (e.g., IM anchor summary) for debugging, but it’s not required.

Recommended simple behavior:

```python
print("=== Theory Council Output ===")
print(result.get("final_synthesis") or "")
```

If you want, you can still print `framed_problem` and `im_summary` separately for debugging, but the user-facing structure should now be in the four sections.

---

## 5. Style & quality guidelines

* **Brevity is now a core feature.**

  * Enforce word/section limits in personas and system prompts.
* Keep code clean and modular:

  * Prompts live in `personas.py`.
  * Graph wiring and state in `graph.py`.
  * Environment and model setup in `config.py`.
* Assume the user will later:

  * Add a UI around this.
  * Possibly plug in RAG or curated theory notes.
* Make sure any changes preserve the ability to log to LangSmith if env vars are set.

The priority is to:

* Deliver **high-quality, theory-informed intervention suggestions**,
* Organized in the four sections the user requested,
* In a format that is easy for a health promotion / IM practitioner to read and use.