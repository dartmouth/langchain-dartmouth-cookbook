# AGENTS.md

## What this repo is

A [Jupyter Book](https://jupyterbook.org/) of example notebooks for the `langchain_dartmouth` library. The notebooks *are* the product — there is no importable Python package, no app, no tests.

## Dev commands

```bash
pip install -r requirements.txt

# Clean stale build cache (do this when notebooks misbehave after edits)
jupyter-book clean langchain_dartmouth_cookbook/

# Build the HTML book (also executes notebooks)
jupyter-book build langchain_dartmouth_cookbook/
# Output: langchain_dartmouth_cookbook/_build/html/
```

No Makefile, pyproject.toml, or package.json exists.

## Adding or editing content

- Notebooks live in `langchain_dartmouth_cookbook/` and are prefixed `NN-` (e.g. `15-structured-output.ipynb`).
- **Always update `_toc.yml`** when adding a new notebook — it is not auto-discovered. `15-structured-output.ipynb` is on disk but not yet in `_toc.yml`.
- Book metadata and execution settings are in `_config.yml`.

## Build / CI quirks

- `execute_notebooks: cache` — the build only re-runs a notebook when its content changes. Run `jupyter-book clean` to force a full re-execution.
- CI (`deploy.yml`) executes notebooks for real, requiring secrets `DARTMOUTH_API_KEY` and `DARTMOUTH_CHAT_API_KEY`. Local builds also need these set in the environment.
- CI deploys to GitHub Pages on push to `main` only (not on PRs).

## Writing style and teaching philosophy

These conventions are consistent across all complete notebooks. New notebooks should match them.

**Tone and voice**
- First-person plural throughout: "Let's explore...", "We can now...", "we have learned..."
- Conversational but precise — collegial peer, not textbook author
- Short to medium sentences, active voice, plain vocabulary; jargon defined on first use

**Concept introduction order**
- Always example-first. Show it working (or deliberately failing), then explain why.
- For multi-step progressions: naive → better → best (e.g. manual string concat → vector store → reranker)
- Anchor new concepts in the previous notebook: "In the previous recipe on tool calling..."

**Code cell pattern**
- 1–3 sentences before a code block explaining *what* will happen and *why*
- Inline comments inside code for *what each step does* (not prose-level explanations)
- One short reaction sentence after the output: "That looks a lot better!", "As we can see..."
- Do not over-explain what the code does in prose if inline comments suffice

**Structure of every notebook**
1. Brief intro paragraph situating the topic and referencing related recipes
2. Headed sections progressing simple → complex
3. `## Summary` section at the end — always ends with *"In this recipe, we have learned..."*, recaps 2–4 key takeaways, no new information

**Callout boxes** (`{note}`, `{hint}`, `{warning}`)
- `{note}` — technical asides that would interrupt prose flow (e.g. explaining a Python concept)
- `{hint}` — "you could go further" or decision-rule guidance (e.g. when to use InMemoryVectorStore vs a production store)
- `{warning}` — reserved for genuine risks (e.g. data privacy when using third-party models); use sparingly

**Target audience**: graduate students / research practitioners who know Python and basic developer tooling but are new to LangChain and the Dartmouth library. Do not explain `for` loops or `pip install`; do explain what a stop token is.

**Incomplete notebook**: `15-structured-output.ipynb` is a code-only skeleton with no prose, no title, and no Summary. It needs intro text, inline comments, callouts, and a Summary before it can be added to `_toc.yml`.

## Dependencies

- `jupyter-book<2.0` — pinned below 2.0; the book is not compatible with v2 syntax.
- `plotly==6.0.0` — pinned; do not upgrade without testing rendering.
- No linting, formatting, or pre-commit hooks are configured.
