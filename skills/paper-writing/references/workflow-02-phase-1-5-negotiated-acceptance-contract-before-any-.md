<!-- EI-WORKFLOW-REFERENCE -->

# Phase 1.5: Negotiated Acceptance Contract (before any writing)

Read this file when the workflow reaches Phase 1.5: Negotiated Acceptance Contract (before any writing) through Phase 2b: Architecture & Illustration Generation. In commands and examples, interpret relative skill paths from the entrypoint directory.

### Phase 1.5: Negotiated Acceptance Contract (before any writing)

The plan says what the paper will contain; the CONTRACT says what "done" means
— a checklist of testable assertions, negotiated ADVERSARIALLY before the first
section is written, and graded at the end. (The plan is the boundary; the
contract is what gets graded.)

1. **Executor proposes.** From `PAPER_PLAN.md` + `NARRATIVE_REPORT.md`, draft
   `PAPER_ACCEPTANCE_CONTRACT.md`: **10–20 testable assertions** covering —
   every headline claim has a named evidence source (file/table); every
   number in the abstract traces to a results file; scope qualifiers the title
   /abstract must carry; figures that must exist and what each must show;
   section-level completeness (e.g. "limitations names ≥2 real limitations,
   not hedges"); venue constraints (page limit, anonymization). Each assertion
   must be CHECKABLE by reading the final PDF + results files — no vibes
   ("writing is clear" is not an assertion; "every acronym is defined at first
   use" is). Fewer than ~10 assertions and the gate rubber-stamps; beyond ~20
   the negotiation stalls on trivia.

2. **Reviewer pushes back** (fresh thread — the negotiation is adversarial):

   ```
   mcp__codex__codex:
     model: gpt-6-astra
     config: {"model_reasoning_effort": "xhigh"}
     prompt: |
       You are negotiating the acceptance contract for a paper BEFORE it is
       written. Read these files directly:
       - Plan: <abs path>/PAPER_PLAN.md
       - Proposed contract: <abs path>/PAPER_ACCEPTANCE_CONTRACT.md
       - Evidence inventory: <abs path>/NARRATIVE_REPORT.md (+ results/ paths)

       Push back on the contract, not the plan: (a) assertions that are
       untestable or vibes — demand a checkable rewrite; (b) missing
       assertions — claims in the plan that no assertion covers, numbers with
       no traceability assertion, foreseeable overclaim risks with no scope
       assertion; (c) assertions the evidence inventory cannot possibly
       satisfy — flag now, not after writing. End with exactly one line:
       CONTRACT_ACCEPTED: yes    or    CONTRACT_ACCEPTED: no
       followed by your numbered revision demands if no.

       === REVIEW SCOPE ===
       Evaluate the actual research question, requested deliverable and applicable
       disciplinary standards. Locate strengths and defects in the supplied evidence;
       do not presume acceptance, rejection or a particular threat model. Distinguish
       observed errors, unsupported claims and optional extensions. Propose the smallest
       adequate correction, citing its failing path, evidence or preserved invariant.
       Keep hypotheses, speculation and unperformed checks explicit. A real boundary
       or reproducibility defect is in scope when it affects this work; unrelated
       infrastructure and speculative redesign are not automatically required.
       Say plainly when something is correct. Do not manufacture findings.
   ```

   A reply with a missing or malformed `CONTRACT_ACCEPTED:` line is treated as
   `no`; request a corrected verdict via `codex-reply` — that correction
   exchange does not consume a negotiation round.

3. **Iterate.** On `no`, revise the contract per the demands and resubmit via
   `mcp__codex__codex-reply` (same thread — the negotiation is one
   conversation). **Max 3 rounds.**

4. **Fallback — never stall the pipeline.** If round 3 still ends in `no`:
   record the unresolved demands verbatim in a "## Disputed" section of the
   contract and mark it `status: contested`. A contested contract is precisely
   the "insert a human when the CONTRACT is wrong" trigger, so it OVERRIDES
   `AUTO_PROCEED` for this one decision: pause and present the dispute for a
   human tie-break. If no human responds (unattended/overnight run), proceed —
   but a contested contract caps the outcome: Phase 6.0 gates on the UNDISPUTED
   assertions and the Final Report must set `Submission-ready: no` with the
   dispute reproduced verbatim; the tie-break happens when the human returns.

**Output:** `PAPER_ACCEPTANCE_CONTRACT.md` (`status: accepted | contested`,
round count, reviewer thread id). The contract is FROZEN once accepted —
Phases 2–5 implement against it; they do not edit it. If writing reveals an
assertion is genuinely wrong (not merely inconvenient), that is a contract
question: surface it at a checkpoint, don't silently rewrite.

**Boundary:** `/paper-claim-audit` (Phases 4.7, 5.5) stays zero-context — the
contract is a WRITER-side gate and is never passed to the claim auditor (its
independence is the point; two different nets).

### Phase 2: Figure Generation

If `— style-ref: <source>` was passed in `$ARGUMENTS` and the helper succeeded above, append `— style-ref: <source>` to every writer-side sub-skill invocation in this pipeline (Phases 1, 2b, 3, 5). Do **not** append it to reviewer/auditor invocations (Phases 4.5, 4.7, 5.5, 5.8).

Invoke `/paper-figure` to generate data-driven plots and tables:

```
/paper-figure "PAPER_PLAN.md"
```

**What this does:**
- Read figure plan from PAPER_PLAN.md
- Generate matplotlib/seaborn plots from JSON/CSV data
- Generate LaTeX comparison tables
- Create `figures/latex_includes.tex` for easy insertion
- GPT-6-Astra reviews figure quality and captions

**Output:** `figures/` directory with PDFs, generation scripts, and LaTeX snippets.

> **Scope:** `paper-figure` covers data plots and comparison tables. Architecture diagrams, pipeline figures, and method illustrations are handled in Phase 2b below.

#### Phase 2b: Architecture & Illustration Generation

**Skip this step entirely if `illustration: false`.**

If the paper plan includes architecture diagrams, pipeline figures, audit cascades, or method illustrations, invoke the appropriate generator based on the `illustration` parameter:

**When `illustration: figurespec`** (default) — invoke `/figure-spec`:
```
/figure-spec "[architecture/workflow description from PAPER_PLAN.md]"
```
- Deterministic JSON → SVG vector rendering (editable, reproducible)
- Best for: system architecture, workflow pipelines, audit cascades, layered topology
- Output: `figures/*.svg` + `figures/*.pdf` (via rsvg-convert) + `figures/specs/*.json`
- No external API, runs fully local

If `— style-ref: <source>` was passed and the helper succeeded above, append `— style-ref: <source>` to the invocation below as well.

**When `illustration: gemini`** — invoke `/paper-illustration`:
```
/paper-illustration "[method description from PAPER_PLAN.md or NARRATIVE_REPORT.md]"
```
- Claude plans → Gemini optimizes → Nano Banana Pro renders → Claude reviews (score ≥ 9)
- Best for: qualitative method illustrations, natural-style diagrams, result grids
- Output: `figures/ai_generated/*.png`
- Requires `GEMINI_API_KEY` environment variable

**When `illustration: mermaid`** — invoke `/mermaid-diagram`:
```
/mermaid-diagram "[method description from PAPER_PLAN.md]"
```
- Generates Mermaid syntax diagrams (flowchart, sequence, class, state, etc.)
- Best for: lightweight flowcharts, state machines, simple sequence diagrams
- Output: `figures/*.mmd` + `figures/*.png`
- Free, no API key needed

**When `illustration: codex-image2`** — invoke `/paper-illustration-image2`:
```
/paper-illustration-image2 "[method description from PAPER_PLAN.md or NARRATIVE_REPORT.md]"
```
- Claude plans → Codex native image generation renders → Claude reviews (same multi-stage workflow as `gemini`, different renderer)
- Best for: users who want a GPT-image-style renderer without needing `GEMINI_API_KEY`; uses your existing Codex / ChatGPT Plus/Pro quota
- Output: `figures/ai_generated/figure_final.png` + `latex_include.tex` + `review_log.json` (emitted via the `/paper-illustration-image2` SKILL's `finalize` step, which delegates to the canonical `paper_illustration_image2.py` helper resolved per [integration-contract §2](../../shared-references/integration-contract.md#2-canonical-helper--one-implementation-not-copy-pasted))
- **Prerequisites** (beyond ARIS's standard Claude Code + Codex coexistence): the local Codex app-server must be signed in (`codex debug app-server send-message-v2 "ping"` succeeds), and the dedicated MCP bridge must be registered — see `mcp-servers/codex-image2/README.md` for the one-time `claude mcp add` command. Delegate the preflight to `/paper-illustration-image2` (which resolves the helper via the canonical chain), or invoke the helper directly via the shim at `tools/paper_illustration_image2.py preflight --workspace .` to confirm before relying on this path.
- **Experimental**: this renderer shells through the Codex debug app-server, which Codex documents as an unstable surface. Prefer `figurespec` or `gemini` for production submission flows until `codex-image2` stabilizes.

**When `illustration: false`** — skip entirely. All non-data figures must be created manually (draw.io, Figma, TikZ) and placed in `figures/` before Phase 3.

**Choosing the right mode:**
- Formal architecture / workflow / topology figures → `figurespec` (default)
- Method concept illustrations with natural style, have `GEMINI_API_KEY` → `gemini`
- Method concept illustrations, prefer ChatGPT Plus/Pro quota over Gemini key → `codex-image2`
- Quick flowchart / state machine → `mermaid`
- Full manual control → `false`

These are complementary, not mutually exclusive: you can run multiple generators for different figures in the same paper by re-invoking with different `illustration` overrides.

**Checkpoint:** List generated vs manual figures.

```
📊 Figures complete:
- Data plots (auto, Phase 2): [list]
- Architecture/illustrations (auto, Phase 2b, mode=<illustration>): [list]
- Manual (need your input): [list]
- LaTeX snippets: figures/latex_includes.tex

[If manual figures needed]: Please add them to figures/ before I proceed.
[If all auto]: Shall I proceed with LaTeX writing?
```

> **Writing invariant (every drafting and revision step):** calibrate each
> claim to its evidence and state it directly; generic caveats live in the
> Limitations section only; writing instructions are never manuscript content
> ("do not mention X" means omit X, not "we do not address X"); tone edits
> never change what the paper knows; preserve the primary question and metrics, report favorable and unfavorable
> findings beside the affected claims, and label retrospective reframing as
> exploratory. Explain tradeoffs only when supported; generic caveats and
> claim-defining limitations are different. `/paper-write` carries the full CONFIDENT PROSE, HONEST LIMITS
> contract.

