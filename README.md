# Theory Council (LangGraph Demo)

Local-first "Theory Council" playground that routes a behavior-change or health promotion problem through multiple theory-inspired agents and synthesizes the results with Intervention Mapping (IM) structure. The backend is powered by LangGraph/LangChain/OpenAI, and a Next.js dashboard lets you watch the agents reason in real time.

## Features
- Problem-framing helper that converts raw text into an IM-friendly brief.
- IM Anchor agent that drafts a compact logic model of the problem & change (Steps 1-2).
- Five theory agents (SCT, SDT, Wise/Belonging, Reasoned Action, Environment & Implementation) that map determinants, methods, and applications into IM Step 2-3 language.
- Debate Moderator plus Theory Selector that critique, rank, and prioritize the most relevant theory lenses.
- Integrator agent that produces a four-section Intervention Mapping-ready synthesis.
- FastAPI server with JSON endpoints for the conversation flow, an optional SSE stream, and LangSmith-aware logging.
- Conversation-first Next.js UI with a persistent “Agent” toggle: OFF behaves like ChatGPT, ON launches the full multi-agent workflow with animated visualizations, then automatically returns to chat mode.
- Typer-based CLI (`python -m theory_council.cli`) for quick terminal runs.

## Project Structure
```
theory-council/
  .gitignore
  .env.example
  requirements.txt
  README.md
  src/
    theory_council/
      config.py
      personas.py
      graph.py
      chat.py
      orchestration.py
      cli.py
    server.py
  frontend/                # Next.js + Tailwind UI
  tests/                   # Pytest API tests
```

## Getting Started
### Backend (FastAPI + LangGraph)
1. **Create & activate a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure environment**
   ```bash
   cp .env.example .env
   # Update OPENAI_API_KEY plus optional LangSmith values
   ```
4. **Run API + streaming server**
   ```bash
   PYTHONPATH=src uvicorn src.server:app --reload --port 8000
   ```

### Frontend (Next.js dashboard)
1. **Install Node deps** (from `frontend/`)
   ```bash
   cd frontend
   npm install
   ```
2. **Expose backend URL**
   ```bash
   cp .env.local.example .env.local  # create if desired
   # set NEXT_PUBLIC_COUNCIL_API=http://localhost:8000
   ```
3. **Start dev server**
   ```bash
   npm run dev
   ```
   The dashboard lives at `http://localhost:3000`. The default view is the chat-style experience with the Agent toggle; when enabled, the panel animates each Intervention Mapping agent run.

## Running the CLI
```bash
python -m theory_council.cli
# or provide text inline
python -m theory_council.cli --problem "Students feel disconnected from first-year STEM courses..."
```

The CLI now guides users through four concise sections:
1. Raw problem text plus the AI framing sent to agents.
2. Debate highlights (including Theory Selector rationale).
3. Intervention Mapping guidance grounded in prioritized theories.
4. Recommended intervention concept(s) derived from the IM blueprint.

## API & Streaming Endpoints
Once `uvicorn src.server:app` is running:

- `POST /conversation/send` — primary conversation endpoint. When `agent_enabled=false`, it routes the turn through a lightweight ChatGPT-style helper. When `agent_enabled=true`, it triggers the multi-agent workflow, returns the four-section output + agent traces, and instructs the UI to toggle Agent mode off again.
- `POST /council/run` — direct synchronous LangGraph execution (bypasses the conversation helper).
- `POST /council/run/stream` — Server-Sent Event (SSE) stream. The response emits `trace` events for each agent followed by a `complete` event mirroring `/council/run`.

All endpoints accept optional `session_id` values so the backend can keep lightweight, in-memory context for each visitor.

## Frontend Dashboard
The Next.js app (`frontend/`) now provides:

- **Conversation page** (`/`) — ChatGPT-like interface with a persistent Agent toggle, animated Theory Council visualization, and the four-section Intervention Mapping report.
- Local session persistence so refreshes keep the transcript, agent output, and toggle state.

Configure `NEXT_PUBLIC_COUNCIL_API` to point at the FastAPI server (default `http://localhost:8000`).

## LangSmith / LangChain Tracing
- Set `LANGCHAIN_TRACING_V2=true` in `.env`.
- Provide `LANGCHAIN_API_KEY`, optional `LANGCHAIN_ENDPOINT`, and `LANGCHAIN_PROJECT` (defaults to `theory-council`).

## Testing
- **Backend**: `pytest` (verifies FastAPI endpoints, chat routing, and SSE output using patched LangGraph responses).
- **Frontend**: `cd frontend && npm run test` (Vitest + Testing Library smoke tests for the core UI components).

## Extending the System
- Add new persona prompts in `src/theory_council/personas.py`.
- Introduce more agents by defining new nodes in `src/theory_council/graph.py` and wiring them into the `StateGraph`.
- Adjust CLI formatting or expose additional options in `src/theory_council/cli.py`.

## Requirements
- Python 3.11+
- OpenAI API access for GPT-4o-mini (agents) and GPT-4.1 (integrator by default).

This demo is intended for local experimentation—feel free to adapt prompts, nodes, or orchestration logic for your own psychological intervention explorations.