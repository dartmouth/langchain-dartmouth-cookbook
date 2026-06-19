# Plan: Agent Orchestration with LangGraph (two recipes)

## Goal

Add two new recipes to the **Agentic Applications** part of the cookbook, fulfilling
the "Looking Ahead: Multi-Agent Workflows" teaser at the end of `14-agents.ipynb`
(multiple agents, conditional branching, human-in-the-loop, state management via
LangGraph):

1. **`16-langgraph-orchestration.ipynb`** — LangGraph `StateGraph` fundamentals,
   anchored by a **routing workflow** (classify a request, then route to a
   specialized node).
2. **`17-multi-agent.ipynb`** — Multi-agent coordination, **comparing the
   supervisor/subagents pattern against the handoffs pattern**.

Recipe 16 establishes the graph mental model; recipe 17 builds on it by treating
agents as nodes/tools in a coordinated system.

## Decisions (confirmed with user)

- **Two separate recipes**, numbered **16** (StateGraph) then **17** (multi-agent).
- Recipe 16 worked example: **routing workflow** (classify → specialize).
- Recipe 17: **compare supervisor/subagents vs. handoffs** side by side.
- **Add `langgraph` to `requirements.txt`** and **render graph diagrams with
  `draw_mermaid_png()`**.
- Model: reuse **`ChatDartmouth(model_name="openai.gpt-oss-120b")`** (consistent
  with recipes 13/14).
- Learning objectives drafted in this plan only; notebook prose stays
  example-first with no visible objectives box (matches existing recipe style).

## Pre-work / verification before writing

LangChain + LangGraph APIs drift. Re-fetch current docs before writing code cells:

- `https://docs.langchain.com/oss/python/langgraph/workflows-agents` (StateGraph,
  routing, orchestrator-worker, `ToolNode`, conditional edges)
- `https://docs.langchain.com/oss/python/langchain/multi-agent` (pattern overview +
  tradeoff tables)
- `https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs` (handoff
  tools, `Command`, `Command.PARENT`, context-engineering caveats)
- `https://docs.langchain.com/oss/python/langchain/multi-agent/subagents` (fetch;
  not yet read — confirm the supervisor/subagent-as-tool API before drafting 17)

Verified API facts (current as of planning, from the docs above):
- `from langgraph.graph import StateGraph, START, END`
- State as `TypedDict`; conditional routing via `add_conditional_edges`.
- `with_structured_output(Route)` on the model drives the router decision (the
  router classifies into a `Literal` step).
- Graph viz: `graph.get_graph().draw_mermaid_png()` wrapped in
  `IPython.display.Image`.
- Handoffs use `langgraph.types.Command` with `goto=...`, `graph=Command.PARENT`,
  and a `ToolMessage`/`AIMessage` pairing to keep history valid — this is
  genuinely fiddly, so the handoff example must stay minimal (2 agents, 1 hop).

### Environment caveat (must resolve during implementation, not planning)

- The planning shell had no working `python`/`pip` and could not import
  `langchain`, `langgraph`, or `langchain_dartmouth`. Before writing code cells,
  confirm in the real build env: (a) whether `langgraph` is already a transitive
  dep of `langchain_dartmouth`, (b) the installed `langchain`/`langgraph`
  versions, and (c) that `draw_mermaid_png()` works there. `draw_mermaid_png()`
  may call a remote mermaid.ink renderer and/or need graphviz — if it fails in
  CI, fall back to printing `get_graph().draw_mermaid()` text. Keep this fallback
  ready even though the chosen approach is PNG rendering.

## Skills to load during implementation

- `grill-with-docs` — already loaded for this planning session (required for every
  new/revised recipe). Re-engage if scope shifts.
- `stop-slop` — load before writing any prose (intros, callouts, summaries).
- `blooms-taxonomy` — consult while drafting the objectives below; do not surface
  them in the notebook.

## Repo conventions to honor (from AGENTS.md + existing notebooks)

- First-person plural, conversational-but-precise voice.
- Example-first: show it working/failing, then explain.
- Anchor in the previous recipe ("In the agents recipe, `create_agent()` hid the
  loop; now we make the control flow explicit...").
- Code cell pattern: 1–3 sentences before each block; inline comments for *what*;
  one short reaction sentence after output.
- Every notebook ends with a `## Summary` section that ends with *"In this recipe,
  we have learned..."* and recaps 2–4 takeaways, no new info.
- Callouts: `{note}` for technical asides, `{hint}` for "go further"/decision
  rules, `{warning}` only for genuine risks.
- Open every notebook with the standard dotenv cell:
  `from dotenv import find_dotenv, load_dotenv` / `load_dotenv(find_dotenv())`.

---

## Recipe 16 — `16-langgraph-orchestration.ipynb`

### Draft learning objectives (plan-only, Bloom's-aligned)
- **Explain** (Understand) why explicit orchestration is needed beyond a single
  `create_agent()` loop.
- **Identify** (Understand) the three building blocks of a LangGraph: state, nodes,
  edges.
- **Construct** (Apply) a `StateGraph` with a typed state and multiple nodes.
- **Implement** (Apply) conditional routing with `add_conditional_edges` driven by
  a structured-output classifier.
- **Differentiate** (Analyze) deterministic workflows from autonomous agents and
  decide when each fits.

### Structure / outline
1. **Intro** — Reference `14-agents.ipynb`: `create_agent()` automated the loop but
   hid the control flow. When we need *predetermined* paths (route this kind of
   request here, that kind there), we want an explicit graph. Introduce LangGraph
   as the orchestration layer named in the previous recipe's "Looking Ahead".
   `{hint}` linking back to 14-agents.
2. **The building blocks** — Brief prose: **state** (shared `TypedDict`), **nodes**
   (functions that read/write state), **edges** (control flow, including
   conditional). `{note}` on how this differs from a plain chain (08-building-chains):
   graphs allow branching and cycles, chains are linear.
3. **Defining the state** — Define the routing `State` `TypedDict`
   (`input`, `decision`, `output`).
4. **The router (classification) node** — A `Route` Pydantic model with a
   `Literal[...]` step; `router = llm.with_structured_output(Route)`; a node that
   classifies the incoming request. Reuse structured-output concepts from
   `15-structured-output.ipynb` (anchor explicitly).
5. **The specialized nodes** — 3 small nodes for the routed task. Use a teaching
   example that's clearly distinct per branch (e.g. **summarize / translate /
   answer-factually**, or the docs' story/joke/poem). Pick a research-flavored
   example to fit the grad-student audience (e.g. "summarize", "explain like I'm
   five", "list key references") — finalize the three branches during writing.
6. **Wiring the graph** — `StateGraph(State)`, `add_node` x4, `add_edge(START, ...)`,
   `add_conditional_edges(router, route_decision, {...})`, edges to `END`,
   `compile()`.
7. **Visualizing the graph** — `Image(graph.get_graph().draw_mermaid_png())` so
   learners *see* the branch structure. (Fallback: print `draw_mermaid()` text.)
8. **Running it** — Invoke with 2–3 inputs that take different branches; show the
   `decision` and `output`. One reaction sentence each.
9. **Workflows vs. agents** — `{hint}` decision rule: deterministic, known paths →
   workflow/graph; open-ended, model-decides-the-path → agent (or multi-agent,
   recipe 17). Tease recipe 17.
10. **Summary** — "In this recipe, we have learned..." + 3–4 takeaways
    (state/nodes/edges, conditional routing, structured output as a router,
    workflow-vs-agent distinction).

### Risks / notes
- Keep the state minimal; do not introduce `Annotated` reducers or `Send` here —
  reserve advanced state for a possible future recipe. One conditional edge is
  enough to teach the concept.

---

## Recipe 17 — `17-multi-agent.ipynb`

### Draft learning objectives (plan-only, Bloom's-aligned)
- **Explain** (Understand) why/when to split work across multiple specialized
  agents instead of one agent with many tools.
- **Build** (Apply) a supervisor that coordinates two specialized subagents.
- **Build** (Apply) a minimal handoff system where one agent transfers control to
  another via a `Command`-returning tool.
- **Compare** (Analyze/Evaluate) supervisor/subagents vs. handoffs across control
  flow, parallelization, direct user interaction, and token cost.
- **Select** (Evaluate) the appropriate pattern for a given scenario.

### Structure / outline
1. **Intro** — Build on recipe 16's graph mental model: a node can itself be an
   *agent*. Motivate multi-agent: one agent with too many tools makes poor tool
   choices; specialization + context isolation help. Reference 14-agents and 16.
2. **The scenario** — Two specialized agents that share a clear, simple domain so
   the comparison is apples-to-apples. Proposed: a **research agent** (a search/
   lookup-style tool) + a **math agent** (reuse the calculator tools from 14). The
   coordinating task requires both (e.g. "Find X, then compute Y from it").
   Finalize the concrete task during writing.
3. **Pattern A — Supervisor / subagents**
   - Build 2 specialized `create_agent()` agents.
   - Build a supervisor that invokes the subagents as tools (confirm exact API via
     the subagents doc fetched in pre-work).
   - Visualize with `draw_mermaid_png()`.
   - Run the coordinating task; show the message trace; one reaction sentence.
   - `{note}`: all routing flows back through the supervisor (centralized control),
     which costs an extra model call but isolates each subagent's context.
4. **Pattern B — Handoffs**
   - Two `create_agent()` agents, each with a handoff tool returning a `Command`
     (`goto`, `graph=Command.PARENT`, paired `ToolMessage`/`AIMessage`).
   - Wire as graph nodes with `add_conditional_edges` (supportable minimal version
     from the handoffs doc).
   - Visualize; run; show how control transfers; one reaction sentence.
   - `{warning}`: handoffs require careful context engineering — you must pass a
     valid `AIMessage`+`ToolMessage` pair or history becomes malformed. Keep the
     example to a single hop to stay teachable.
5. **Comparing the patterns** — A short markdown table summarizing the tradeoffs
   (distributed development, parallelization, multi-hop, direct user interaction,
   relative model-call cost) adapted from the LangChain multi-agent docs. Prose
   decision rule. `{hint}`: other patterns exist (router, skills, Deep Agents) —
   link out, don't implement.
6. **Summary** — "In this recipe, we have learned..." + 3–4 takeaways (why
   multi-agent, supervisor pattern, handoffs pattern, how to choose).

### Risks / notes
- Handoffs are the hardest part. Budget extra time to get a *working, minimal*
  example. If the full subgraph handoff proves too fiddly/long for a teaching
  notebook, fall back to the **single-agent-with-middleware** handoff variant
  (also in the docs) which is simpler — decide during implementation and note the
  choice. Do NOT ship a broken/over-long handoff example.
- Keep both patterns on the *same* two-agent scenario so the comparison is fair.
- Watch total notebook length; this recipe has two full implementations plus a
  comparison. Trim subagent/handoff scaffolding to the minimum that still runs.

---

## Cross-cutting implementation steps

1. **Update `requirements.txt`** — add `langgraph` (pin a version after checking
   what installs cleanly with the current `langchain_dartmouth`; record the pin).
2. **Write `16-langgraph-orchestration.ipynb`** per outline above.
3. **Write `17-multi-agent.ipynb`** per outline above.
4. **Update `_toc.yml`** — add both files under the `Agentic Applications` part,
   after `15-structured-output`. (Note: `15-structured-output` is currently listed
   in `_toc.yml` but is an incomplete skeleton per AGENTS.md — do **not** alter its
   entry as part of this work unless asked.)
5. **Build locally to execute notebooks** (needs `DARTMOUTH_API_KEY` and
   `DARTMOUTH_CHAT_API_KEY` in env):
   - `jupyter-book clean langchain_dartmouth_cookbook/`
   - `jupyter-book build langchain_dartmouth_cookbook/`
   - Confirm both new notebooks execute end-to-end and `draw_mermaid_png()`
     renders. If PNG rendering fails, switch those cells to `draw_mermaid()` text
     output and rebuild.
6. **Apply `stop-slop`** pass over all new prose before finalizing.

## Out of scope (note for future recipes)
- Persistence/checkpointers, `InMemorySaver`, threads.
- Human-in-the-loop interrupts.
- `Send` API / map-reduce orchestrator-worker fan-out.
- Streaming graph execution.
- Deep Agents, skills, and the router multi-agent pattern (mention/link only).
These are good candidates for follow-on recipes but would overload these two.

## Open questions / assumptions
- Exact branch tasks for recipe 16's router and the concrete coordinating task for
  recipe 17 are left to finalize during writing (placeholders proposed above).
- `langgraph` version pin to be set once a clean install is confirmed.
