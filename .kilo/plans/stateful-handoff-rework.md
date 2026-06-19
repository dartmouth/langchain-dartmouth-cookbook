# Plan: Rework the handoff example in `17-multi-agent.ipynb` into a stateful, four-turn conversation

## Goal

Replace the current single-shot handoff demo in **Pattern B** of
`17-multi-agent.ipynb` with a **stateful, bidirectional, four-turn conversation**
that actually shows what the handoffs pattern is for: control passing back and
forth between two agents across turns, with each agent staying "active" until it
hands off.

The four turns to demonstrate, in order:

1. **Research answers directly.** The research agent handles a library question
   with no handoff.
2. **Research hands off to math.** A calculation forces `transfer_to_math`; the
   math agent computes and answers.
3. **Math answers directly.** The math agent is now active and answers a second
   calculation without any handoff.
4. **Math hands off to research.** A library question forces
   `transfer_to_research`; control returns to the research agent.

## Why the current example is weak

The current Pattern B does one `.invoke()` with a single calculation. The
research front desk immediately calls `transfer_to_math`, math answers, done. It
shows the *mechanism* of a single transfer but not the *point* of handoffs:
agents taking turns with the user across a multi-turn conversation, where the
"active" agent persists between turns. It is also one-directional (only
research -> math), so it never shows control coming back.

## Design (confirmed with user)

Two design decisions were grilled and confirmed:

1. **Manual state-passing instead of a checkpointer.** The caller threads the
   returned state back into the next `.invoke()`. This keeps
   persistence/checkpointers/threads **out of scope** (consistent with the
   original recipe boundary) and makes the state flow *visible* in the notebook
   rather than hidden behind a `thread_id`. `active_agent` is already a field on
   `MultiAgentState`, so memory of who is active rides along in the same dict.

2. **Add a conditional entry point.** Manual state-passing solves *memory* but
   not *where execution re-enters*. The current `add_edge(START, "research_agent")`
   hard-wires every invocation to start at research, which would break turns 3
   and 4. Replace it with a conditional entry edge that reads `active_agent`:

   ```python
   def route_initial(state):
       return state.get("active_agent", "research_agent")
   builder.add_conditional_edges(START, route_initial, ["research_agent", "math_agent"])
   ```

   Narrative: the state *remembers* who is active (memory); the entry router
   *resumes* with that agent (control).

## Confirmed turn script

- **Turn 1** — "How many volumes did Baker Library open with?" -> research calls
  `lookup_library_fact`, answers, no handoff. (`active_agent` -> research)
- **Turn 2** — "Multiply that by 2." -> research calls `transfer_to_math`; math
  calls `multiply`, answers. (`active_agent` -> math) Relies on turn 1's number
  being in the carried-forward message history — reinforces why state-passing
  matters.
- **Turn 3** — "What is that plus 1000?" -> math is active (entry router sends us
  there), calls `add`, answers, no handoff. (`active_agent` stays math)
- **Turn 4** — "Which library received a $30 million gift, and in what year?" ->
  math calls `transfer_to_research`; research calls `lookup_library_fact`
  (topic 'berry'), answers. (`active_agent` -> research)

## Code changes required (all within Pattern B of `17-multi-agent.ipynb`)

### 1. Add a second, symmetric handoff tool
Add `transfer_to_research` mirroring the existing `transfer_to_math`: same
`Command` shape, `goto="research_agent"`, `active_agent="research_agent"`, same
`AIMessage`+`ToolMessage` pairing. Consider factoring the
"find last AIMessage" line into a tiny helper to avoid duplicating it across two
tools (optional; keep it readable for teaching).

### 2. Give both agents a handoff tool and tighten prompts
- **Research agent**: tools `[lookup_library_fact, transfer_to_math]`. Prompt:
  answers library questions, *cannot* do arithmetic, must call `transfer_to_math`
  for any calculation and not attempt math itself.
- **Math agent**: tools `[add, subtract, multiply, transfer_to_research]`.
  Prompt: does arithmetic, has *no* library knowledge and cannot look facts up,
  must call `transfer_to_research` for any library fact and not guess.

  The "cannot / must not guess" framing is load-bearing for turns 2 and 4 — see
  Risks.

### 3. Replace the fixed entry edge with a conditional entry point
Add `route_initial` and wire `add_conditional_edges(START, route_initial,
["research_agent", "math_agent"])`. Remove the old
`add_edge(START, "research_agent")`.

### 4. Make routing bidirectional
`route_after_agent` already returns `state.get("active_agent", ...)`; widen its
return type and the edge targets so **both** agent nodes can route to **either**
agent or `END`:

```python
builder.add_conditional_edges("research_agent", route_after_agent,
                              ["research_agent", "math_agent", END])
builder.add_conditional_edges("math_agent", route_after_agent,
                              ["research_agent", "math_agent", END])
```

(The current code only allows `research_agent -> {math_agent, END}` and
`math_agent -> END`.)

### 5. Drive the four turns with explicit manual state-passing
Replace the single `handoff_task` invoke with a loop (or four explicit cells)
that threads state forward:

```python
state = {"messages": []}
for user_msg in turns:
    state["messages"] = state["messages"] + [{"role": "user", "content": user_msg}]
    state = graph.invoke(state)
    # show active_agent + this turn's messages
```

For teaching clarity, prefer **four separate code cells** (one per turn) over a
loop, each followed by a one-sentence reaction, so the reader sees each
transition and the `active_agent` value change. Decide loop-vs-cells during
implementation based on output length; four cells is the leaning choice.

**Turn display (confirmed with user): full `pretty_print()` for every turn.**
Each turn's cell prints the complete message trace for that turn (every
`HumanMessage`/`AIMessage`/`ToolMessage`, including tool calls and the handoff
`ToolMessage`), plus the resulting `active_agent`. Do not trim to a summary view.
Because each `.invoke()` returns the *accumulated* history, iterate only over the
messages produced in the current turn (slice from the prior turn's length) so the
four cells don't reprint the entire growing conversation each time. Confirm the
slicing during the live verification run.

### 6. Update the static `{mermaid}` concept diagram
The existing Pattern B concept flowchart is one-directional
(research -> answer, research -> math -> answer). Update it to show the
bidirectional, stateful nature: both agents can answer the user, and either can
hand off to the other. Sketch:

```{mermaid}
flowchart LR
    user([user]) <--> research[research agent]
    user([user]) <--> math[math agent]
    research <-->|transfer| math
```

(Finalize exact arrows during writing; the point is to show two-way transfer and
that whichever agent is active talks to the user directly.)

### 7. Update the compiled-graph diagram prose
The `draw_mermaid_png()` of the compiled graph will now show edges in both
directions plus the conditional entry. Update the one-line prose before/after it
to describe the back-and-forth rather than a single research -> math arrow.

### 8. Rewrite the surrounding prose
- Intro to Pattern B: motivate the multi-turn, stateful framing (an agent stays
  active across turns until it hands off).
- The `{warning}` about `AIMessage`/`ToolMessage` pairing stays — still true and
  now applies to both handoff tools. Drop the "we keep this example to a single
  transfer" sentence since we now do several.
- Add a short `{note}` explaining the manual state-passing choice and contrasting
  it with checkpointers/threads (link out, mark as a future topic), so we stay
  honest about scope.
- Closing prose: tie the four turns back to the comparison table's "direct user
  interaction" and "multi-hop" columns.

## Pre-implementation verification (REQUIRED, before editing the notebook)

The previous build session already confirmed the core APIs
(`Command`/`Command.PARENT`, `ToolRuntime.tool_call_id`/`.state`,
`AgentState` subclassing, `create_agent`, conditional edges, `draw_mermaid_png`).
What is **not** yet verified is the new four-turn behavior. Before touching the
notebook, run a throwaway script (outside plan mode) against the live model to
confirm:

1. **Manual state round-trip is clean.** Threading `result` back into the next
   `.invoke()` and appending the new user message does not duplicate messages or
   break the `AIMessage`/`ToolMessage` pairing. Inspect the full message list
   after all four turns.
2. **Conditional entry point resumes correctly.** Turn 3 must enter at
   `math_agent` (not research) given `active_agent == "math_agent"`.
3. **Turn 2 uses carried context.** Math doubles 240000 (from turn 1), giving
   480000 — proving the number survived in history.
4. **Turn 4 (the fragile one) fires `transfer_to_research`** rather than the math
   agent answering the library question from its own parametric knowledge.

Only proceed to edit the notebook once all four turns produce a clean, correct,
reproducible trace. If turn 4 is unreliable, iterate on the math agent's prompt
(stronger "you have NO library knowledge / do not guess" framing) and, if still
shaky, pick a turn-4 question the model is less likely to know cold. Do NOT ship
a handoff example where the agent answers instead of transferring.

## Risks / notes

- **Turn 4 reliability is the top risk.** In the original build, `gpt-oss-120b`
  was eager to hand off but reluctant to do lookup-then-handoff, and prone to
  answering from parametric knowledge. The math->research turn depends on the
  model choosing `transfer_to_research` over guessing. Mitigation: forcing prompt
  + a fact that's specific enough to discourage guessing (the $30M/1992 Berry
  gift maps cleanly to the 'berry' topic). `temperature=0.0` is already set.
- **Turn 2 also has a lookup-then-handoff shape**, but here the handoff is the
  *only* action research needs (it can't multiply), so it's lower risk than the
  original "look up THEN hand off in one turn" framing. The number comes from
  turn 1's history, not a turn-2 lookup.
- **Notebook length.** Pattern B grows from ~1 invocation to 4 turns plus a
  second handoff tool and bidirectional routing. User wants full `pretty_print()`
  per turn, so manage length by printing **only the current turn's new messages**
  (slice from the prior history length) rather than the whole accumulated
  conversation each time, and keep each turn's reaction prose to one sentence.
- **Scope honesty.** This deliberately uses manual state-passing to *avoid*
  checkpointers/threads. Call that out in a `{note}` so readers know the
  production option exists and why we didn't use it here.
- **Pattern asymmetry.** Supervisor stays one `.invoke()`; handoffs becomes
  multi-turn. This asymmetry is intentional and mirrors reality (handoffs shine
  for multi-turn direct user interaction) — lean into it in the prose rather than
  forcing visual parity.

## Out of scope (unchanged)

- Checkpointers/`InMemorySaver`/`thread_id` (we use manual state-passing instead;
  mention as a future option only).
- Human-in-the-loop interrupts, `Send`/map-reduce, streaming.
- Any change to Pattern A (supervisor) or the comparison table beyond the closing
  prose tie-in.

## Validation after implementation

1. Execute the notebook end-to-end (`jupyter nbconvert --execute`) with the env
   keys set; confirm 0 errors and that all four turns show the intended
   `active_agent` transitions and tool calls.
2. Confirm both `{mermaid}` concept diagram and the `draw_mermaid_png()` compiled
   diagram render.
3. `jupyter-book build` succeeds with no new content warnings.
4. stop-slop pass over all new/changed prose.
