# Plan: Finish `15-structured-output.ipynb`

## Goal

Turn the existing code-only skeleton into a complete recipe matching the cookbook's
style. The throughline: **structured output automates the same loop we did by hand in
`05-output-parsing.ipynb`** — instruct the model to produce a specific shape, and if the
output has syntax/schema problems, send it back to the model and try again. `create_agent`
with `response_format` does that loop for us.

## Context

- The skeleton (`15-structured-output.ipynb`) deliberately mirrors `05-output-parsing.ipynb`:
  same Baker-Berry text, same "extract a timeline" task, same prompt string. This reuse is
  intentional and should be made explicit in the prose.
- Reader background by this point in the book:
  - `05` — manual approach: JSON-formatting prompt + `JsonOutputParser`, and the observation
    that re-running can produce drifting formats (the implicit "loop").
  - `13-tool-calling` / `14-agents` — `create_agent` automates the tool trigger → execute →
    feed-result-back loop; readers have already inspected `result["messages"]` via
    `pretty_print()`.
- LangChain behavior (from docs.langchain.com/oss/python/langchain/structured-output):
  - Passing a schema *type* to `response_format` auto-selects **ProviderStrategy** (native
    structured output) when the model supports it, else **ToolStrategy** (tool-calling).
  - Under **ToolStrategy**, the agent validates the structured output and, on a
    multiple-output or schema-validation error, returns an error `ToolMessage` and
    **re-prompts the model to retry** (`handle_errors=True` by default). This retry IS the
    automated loop the notebook is teaching.
  - Result is returned in `result["structured_response"]`.
  - Dataclass schema → returns a `dict`; the current code uses `timeline.events` /
    `event.year` attribute access, which assumes an *object*, not a dict. **This is a likely
    bug to verify on build** (see Risks).

## Design decisions (resolved with user)

1. **Anchor the loop conceptually**, not by forcing a failure. Keep the happy-path code
   simple; explain in prose + a callout that the agent re-prompts the model on
   schema/syntax errors — the same loop `05` did manually.
2. **Surface the loop in code** by inspecting `result["messages"]` with `pretty_print()`,
   reusing the inspection pattern from `14-agents`.
3. **Explicit callback to `05`** in both intro and Summary: we hand-wrote a JSON prompt +
   parser and re-ran when the format drifted; structured output automates that whole cycle.
4. **Stay focused on the dataclass approach**; add one `{hint}` callout noting that the
   schema can also be defined as a Pydantic model / TypedDict / JSON schema, with a link to
   the docs. No second full example.

## Notebook structure (final)

Match the house structure: intro → simple→complex sections → `## Summary` ending with
"In this recipe, we have learned...". First-person plural, example-first, 1–3 sentences
before each code cell, one short reaction sentence after output.

1. **Title + intro (markdown)** — `# Structured output`. Situate the topic and reference
   `05`: there we manually engineered a JSON prompt and wrote a parser, and noticed the
   model's format could drift between runs, forcing a re-run. Frame this recipe as letting
   LangChain handle that loop for us. Reuse the same Baker-Berry timeline task.

2. **Input data (markdown + existing code cell)** — keep the `unstructured_text` cell; one
   or two sentences noting it's the same passage from `05`.

3. **Setup (existing code cell)** — `ChatDartmouth` import + `load_dotenv`. Brief lead-in.

4. **Defining the output shape (markdown + existing dataclass cell)** — introduce the idea
   of describing the *shape* we want with a schema. Inline comments already document the
   fields; add 1–3 sentences of prose. Note the docstrings/comments help the model.
   - Add a `{hint}` callout: the schema can also be a Pydantic model, a `TypedDict`, or a
     raw JSON schema — link to
     `https://docs.langchain.com/oss/python/langchain/structured-output`.

5. **Creating the agent (markdown + existing `create_agent` cell)** — explain
   `response_format=Timeline`: we hand the agent the schema and it takes responsibility for
   getting the model to fill it in. Reuse the exact same `prompt` string as `05` (already
   present) and call that reuse out.

6. **Invoking + the automated loop (markdown + existing invoke cell + NEW message-trace
   cell)** —
   - Prose: invoke the agent, get `result["structured_response"]`.
   - **NEW code cell**: `for msg in response["messages"]: msg.pretty_print()` to show the
     under-the-hood AIMessage → ToolMessage sequence.
   - Prose after output: connect to `05` and `14` — when the model's output doesn't fit the
     schema, the agent feeds the error back and asks it to try again, exactly the manual
     re-run loop from `05`, now automatic. Add a `{note}` callout explaining the
     ProviderStrategy vs ToolStrategy auto-selection at a high level and that the retry
     behavior lives in the tool-calling strategy.

7. **Displaying the timeline (existing print-loop cell)** — keep, with a one-line reaction.
   **Verify field access** against the actual returned type (dict vs object) and fix if
   needed (see Risks).

8. **`## Summary` (markdown)** — recap 2–4 takeaways, end with "In this recipe, we have
   learned...":
   - Structured output lets us declare the desired *shape* (a schema) instead of writing a
     format prompt + parser by hand.
   - `create_agent(response_format=...)` returns parsed data in
     `result["structured_response"]`.
   - Under the hood it automates the validate → re-prompt loop we did manually in `05`.
   - The schema can be defined multiple ways (dataclass / Pydantic / TypedDict / JSON).

## Files to change

- `langchain_dartmouth_cookbook/15-structured-output.ipynb` — add markdown cells, inline
  prose, callouts, the message-trace cell, and the Summary; verify/fix field access.
- `langchain_dartmouth_cookbook/_toc.yml` — add `- file: 15-structured-output` under the
  **Agentic Applications** caption (after `14-agents`), since structured output here builds
  on `create_agent`.

## Validation

1. Set `DARTMOUTH_CHAT_API_KEY` / `DARTMOUTH_API_KEY` in the environment.
2. `jupyter-book clean langchain_dartmouth_cookbook/` then
   `jupyter-book build langchain_dartmouth_cookbook/` to execute the notebook end-to-end and
   confirm the new cells run and render (callouts, message trace, timeline output).
3. Confirm the notebook appears in the built TOC.

## Risks / things to verify during implementation

- **Dataclass returns a dict, not an object.** Per the docs, a dataclass schema yields a
  `dict` in `structured_response`. The skeleton's `timeline.events` / `event.year` assumes
  attribute access. During implementation, run the cell and either (a) switch to dict access
  (`timeline["events"]`, `event["year"]`) or (b) switch the schema to a Pydantic `BaseModel`
  if attribute access is desired. Pick whichever keeps the field-access cell cleanest; if
  switching to Pydantic, update the "Defining the output shape" prose accordingly. Decide
  based on actual build output, not assumption.
- **Strategy auto-selection is model-dependent.** Whether `openai.gpt-oss-120b` uses
  Provider vs Tool strategy affects what the message trace shows. Keep the loop explanation
  conceptual (callout) so the prose stays correct regardless; describe the message trace in
  terms of what actually prints after the build.
- **CI determinism.** We are not forcing a failure, so the happy path should be stable.
  Avoid asserting on exact message counts in prose.
- **API freshness.** Re-check `https://docs.langchain.com/oss/python/langchain/structured-output`
  and `llms.txt` before finalizing code, per AGENTS.md.

## Skills to apply during implementation

- `stop-slop` — run over all new prose (intro, callouts, Summary, inline reactions).
- Match house style from AGENTS.md (first-person plural, example-first, callout conventions).
