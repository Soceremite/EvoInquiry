---
name: meta-optimize
description: "Analyze toolkit usage logs and propose changes to skill instructions, reviewer prompts, or workflow defaults. Use for evidence-based harness optimization."
argument-hint: "[target-skill-or-all]"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.
<!-- EVO-INQUIRY:END -->


# Meta-Optimize: Outer-Loop Harness Optimization for ARIS

Analyze accumulated usage logs and propose optimizations for: **$ARGUMENTS**

## Producer boundary

This skill proposes and stages; it never changes the installed corpus or invokes
its own landing. Write only reports, evidence and patches under `.ei/meta/`.
Tool availability is not a filesystem sandbox: retain this workflow boundary and
do not claim that frontmatter alone technically prevents all writes. A separate,
human-invoked [meta-apply](../meta-apply/SKILL.md) performs fresh landing review on
the actual staged diff and preserves same-family provisional status.

## Context

ARIS is a **research harness** — a system of skills, bridges, workflows, and artifact contracts that wraps around LLMs to orchestrate research. This skill implements a prototype **outer loop** that observes how the harness is used and proposes improvements to the harness itself (not to the research artifacts it produces).

Inspired by Meta-Harness (Lee et al., 2026): the key insight is that harness design matters as much as model weights, and harness engineering can be partially automated by logging execution traces and using them to guide improvements.

## What This Skill Optimizes (Harness Components)

| Component | Example | Optimizable? |
|-----------|---------|:---:|
| SKILL.md prompts | Reviewer instructions, quality gates, step descriptions | Yes |
| Default parameters | `difficulty: medium`, `MAX_ROUNDS: 4`, `threshold: 6/10` | Yes |
| Convergence rules | When to stop the review loop, retry counts | Yes |
| Workflow ordering | Skill chain sequence within a workflow | Yes |
| Artifact schemas | What fields go in EXPERIMENT_LOG.md, idea-stage/IDEA_REPORT.md | Cautious |
| MCP bridge config | Which reviewer model, routing rules | No (infra) |

**Not optimized**: The research artifacts themselves (papers, code, experiments). That's what the regular workflows do.

## Prerequisites

1. **Logging must be active.** Codex mirror installs do not create Claude Code hooks. Provide `.ei/meta/events.jsonl` from a Codex-compatible event logger, an external wrapper, or a manually exported trace log before running this skill.
2. **Relevant evidence.** Five completed independent task traces are a collection heuristic, not five skill calls or a proof of sufficiency. A specific reproducible defect can justify a narrow proposal sooner; broad defaults need broader evidence. Report actual coverage and missing outcomes.

## Workflow

### Step 0: Check Data Availability

Resolve the existing state namespace and read `.ei/meta/events.jsonl`. Use the
installed package's `tools/research_events.py --root <project> --summary` for
read-only counts. Keep recorded invocations, skill-reference candidates, completed
turns and completed workflows distinct. Legacy hooks and exported Codex traces
have different observable fields; unknown outcomes remain unknown. Missing logs
are missing evidence, not permission to manufacture examples or scan private history.

For an explicit project-relative Codex export, the Codex-compatible event logger
is `tools/research_events.py --root <project> --source <trace.jsonl> --session <id>`.
It imports source-bound observations without raw prompts, commands or outputs.
No installed Codex session hook is implied. Keep original traces local under
existing access policy. A command path mention is not proof of skill compliance.

### Step 1: Analyze Usage Patterns

Read `.ei/meta/events.jsonl` and compute:

**Frequency analysis:**
- Which skills are invoked most often?
- Which slash commands do users type most?
- What parameter overrides are most common? (These suggest bad defaults.)

**Failure analysis:**
- Which tools fail most often? In which skills?
- What error patterns repeat? (OOM, import, compilation, timeout)
- How many auto-debug retries per workflow run?

**Convergence analysis (for auto-review-loop):**
- Average rounds to reach threshold
- Score trajectory shape (fast improvement? plateau? oscillation?)
- Which review round catches the most critical issues?
- Do users override difficulty mid-run?

**Human intervention analysis:**
- Where do users interrupt with manual prompts during workflows?
- What manual corrections do users make most? (These indicate skill gaps.)

**Model-delta analysis (harness diet):**
- Has the session model or the pinned reviewer model changed since a skill's
  SKILL.md was last touched? A model bump is a **trigger to re-read, not
  evidence by itself**: a deletion proposal must cite TARGET-SPECIFIC evidence
  (a capability-specific release note, or repeated post-bump event-log behavior
  showing the scaffold is unused). **Never deletion candidates**: privilege
  boundaries, acceptance/review gates, corpus/provenance rules, output
  contracts, safety checks. The diet targets model-compensation scaffolding
  only — a capability the new model has natively is pure overhead. A harness
  that only ever grows is a harness nobody is re-reading.

**Trigger-rate analysis (measured, not from the event log):** the log shows
which skills were USED, not which were WANTED-but-omitted. Mainline ships
`tools/meta_opt/trigger_eval.py`, which measures Claude Code's skill triggering
via `claude -p` probes (trigger / confusion / miss). It is Claude-Code-specific
— use the separate native Codex behavior harness below for Codex;
this Claude-only selection probe is not a step you run as a Codex probe.
Measure-only regardless: a low rate is INPUT to a proposal, never a self-applied
rewrite; the confusion matrix (which sibling a query lands on) points at
disambiguation, not "make it pushier".

For Codex, use the existing `tools/evaluate_skill_behavior.py` with the actual
installed catalog for bounded routing and task-behavior cases, including negative
cases. Preserve native discovery, source snapshots, every failed or timed-out
attempt, and independently assess the traces/artifacts against a frozen rubric.
A command reading a skill is an access signal; behavior needs outcome assessment.
The Claude-only trigger probe above is not a Codex probe.

Present findings as a structured summary table.

### Paired candidate evaluation

Before using a proposed change to claim improvement, freeze development/held-out
case IDs, independent repetitions, model/provider/effort, budgets, harness and
rubric. Pin baseline and candidate environment/discovery snapshots. Use the same
request and fixture for each pair; reusing a test task during revision makes it
part of development, so replace its held-out role. More forceful triggering alone
is not better behavior. Report unnecessary activations as well as omissions.

`tools/meta_opt/compare_candidates.py --root <study> --request <request.json>`
consumes a fixed `protocol_ref`, existing native-harness run records and separate
source-bound assessments. Its Python docstring specifies the input fields. Keep
all declared attempts, failures, timeouts, unassessed outcomes, improvements and
regressions. Fewer than two repeats or no held-out tasks is explicitly insufficient
for its candidate signal. This minimum is not a statistical sufficiency rule.

The comparison report is advisory. It cannot establish reviewer independence,
discover undisclosed attempts, authorize landing, or certify general RSI. A faster
or cheaper candidate still needs quality and scope checks. Preserve the old
version and define rollback conditions before a human-authorized landing.

### Step 1.5: Name the Current Bottleneck

Synthesize the Step-1 analyses into **one sentence naming the single
most-limiting pipeline stage right now** — e.g. "planning", "verification
quality", "experiment execution reliability", "writing polish" — with evidence.
The bottleneck always moves: coding → planning → verification → taste. Step 2's
ranked table should read as sub-fixes for this one named constraint.

Append the verdict to the append-only ledger `.ei/meta/bottleneck_log.jsonl`
(never edit or delete prior lines — succession history is the point):

```bash
mkdir -p .ei/meta
# json.dumps, NOT hand-interpolated shell strings: bottleneck/evidence are
# natural language — a stray quote must not break the JSONL (or the shell).
python3 - <<'PY'
import json, datetime
entry = {
    "ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    "cycle": 3,
    "bottleneck": "verification quality",
    "evidence": "review rounds plateau at 6/10 while tool failures are rare",
    "top_patch_ids": ["P1", "P2"],
}
with open(".ei/meta/bottleneck_log.jsonl", "a", encoding="utf-8") as fh:
    fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
PY
```

On the next run, read the last line first and open the report by stating
whether that bottleneck was resolved and what it has moved to.

### Step 2: Identify Optimization Targets

Based on Step 1, rank optimization opportunities by expected impact:

```markdown
## Optimization Opportunities (ranked)

| # | Target | Signal | Proposed Change | Expected Impact |
|---|--------|--------|-----------------|-----------------|
| 1 | auto-review-loop default threshold | Users override to 7/10 in 60% of runs | Change default from 6/10 to 7/10 | Fewer manual overrides |
| 2 | experiment-bridge retry count | 40% of runs hit max retries on OOM | Add OOM-specific recovery (reduce batch size) | Fewer failed experiments |
| 3 | paper-write de-AI patterns | Users manually fix "delve" in 80% of runs | Add "delve" to default watchword list | Fewer manual edits |
| 4 | experiment-bridge Phase-2 hand-holding steps | Model bump; scaffold untouched for 2 generations; zero failures in the guarded steps | **DELETE steps N–M — the new model does this unprompted** | Smaller harness, less drift surface |
```

The Proposed-Change column is explicitly allowed to be a **deletion** — "DELETE
step N, new model does this for free" is a first-class optimization.

If `$ARGUMENTS` specifies a target skill, focus analysis on that skill only.
If `$ARGUMENTS` is empty or "all", analyze all skills with sufficient data.

### Step 3: Generate Patch Proposals

For each optimization target, generate a concrete diff:

```diff
--- a/skills/auto-review-loop/SKILL.md
+++ b/skills/auto-review-loop/SKILL.md
@@ -15,7 +15,7 @@
 ## Constants
 
-- **SCORE_THRESHOLD = 6** — Minimum review score to accept.
+- **SCORE_THRESHOLD = 7** — Minimum review score to accept. (Raised based on usage data: 60% of users overrode to 7+.)
```

**Rules for patch generation:**
- One patch per optimization target
- Each patch must include a comment explaining WHY (with data from the log)
- Patches must be minimal — change only what the data supports
- Never change artifact schemas or MCP bridge config in v1
- Never change behavior that would break existing user workflows
- **Anti-self-poisoning screen:** resolve `$ARIS_REPO` from
  `.ei/installed-skills-codex.txt`, then run
  `$ARIS_REPO/tools/capture_filter.py` (or project-local
  `tools/capture_filter.py`) against each proposed patch rationale. If it flags
  an environment failure, transient error, negative tool-capability claim, or
  one-off narrative, rewrite the proposal to the fix/config/workaround or drop
  it. Warn-and-skip only when the helper cannot be resolved. See
  [`capture-antipatterns.md`](../shared-references/capture-antipatterns.md).

### Step 4: Fresh-Agent Review of Patches (same-family provisional)

Send each patch to GPT-6-Astra xhigh for adversarial review:

```text
spawn_agent:
  model: gpt-6-astra
  reasoning_effort: xhigh
  message: |
    You are reviewing a proposed optimization to an ARIS SKILL.md file.
    
    ## Original Skill (relevant section)
    [paste original]
    
    ## Proposed Patch
    [paste diff]
    
    ## Evidence from Usage Log
    [paste summary stats]
    
    Review this patch:
    1. Does the evidence support the change?
    2. Could this change hurt other use cases?
    3. Is the change minimal and safe?
    4. Score 1-10: should this be applied?
    
    If score < 7, explain what additional evidence would be needed.

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

### Step 5: Present Results

Output a structured report:

```markdown
# ARIS Meta-Optimization Report

**Date**: [today]
**Data**: [N] events, [M] skill invocations, [K] sessions
**Target**: [skill name or "all"]

## Current Bottleneck

**[one-phrase name]** — [one-line evidence]. Prior cycle's bottleneck: [name —
resolved by <patch ids> / unresolved / first recorded cycle]. (Ledger:
`.ei/meta/bottleneck_log.jsonl`)

## Proposed Changes

### Change 1: [title]
- **Target**: [skill/file:line]
- **Signal**: [what the data shows]
- **Patch**: [diff]
- **Reviewer Score**: [X/10]
- **Reviewer Notes**: [summary]
- **Status**: ✅ Recommended / ⚠️ Needs more data / ❌ Rejected

### Change 2: ...

## Changes NOT Made (insufficient evidence)
- [pattern observed but too few samples]

## Recommendations
- [ ] Apply Change 1 (reviewer approved)
- [ ] Collect more data for Change 3 (need N more runs)
- [ ] Consider manual review of Change 2

## Next Steps
This producer ends with a report and staged candidates. The human invokes
`/meta-apply` for a selected patch; its fresh landing review remains required.
```

### Step 6: Stage selected patches; never apply here

Write each selected diff under `.ei/meta/pending/` with its target, author model,
source evidence and an explicitly advisory pre-screen. Bind any comparison report
to the staged patch and tested candidate snapshot. Producer-written scores and
`CANDIDATE_SIGNAL` are not landing verdicts. Report the staged paths; leave backups,
fresh landing review, application, provenance stamping and rollback logging to the
separately invoked [meta-apply](../meta-apply/SKILL.md). Never invoke it yourself.

## Key Rules

- **Log-driven, not speculative.** Every proposed change must cite specific data from the event log. No "I think this would be better."
- **Minimal patches.** Change one thing at a time. Don't rewrite entire skills — the one sanctioned large edit is a scaffolding **deletion** backed by TARGET-SPECIFIC model-delta evidence (capability-specific release note, or repeated post-bump event-log behavior; a model-name change alone is never sufficient). Privilege boundaries, acceptance gates, corpus/provenance rules, output contracts, and safety checks are never deletion candidates. Deletions go through the same review + approval gates.
- **Reviewer-gated.** Every patch goes through fresh-agent same-family provisional review before recommendation.
- **Reversible.** Always back up before applying. Always log what changed.
- **User-approved.** Never auto-apply. Present, explain, let the user decide.
- **Honest about uncertainty.** If the data is insufficient, say so. Don't optimize on noise.
- **Portable.** Optimizations should improve the skill for all users, not just one user's style. If a change seems user-specific, flag it.

## Event Schema Reference

The log at `.ei/meta/events.jsonl` contains JSONL records with these shapes:

```jsonl
{"ts":"...","session":"...","event":"skill_invoke","skill":"auto-review-loop","args":"difficulty: hard"}
{"ts":"...","session":"...","event":"PostToolUse","tool":"Bash","input_summary":"pdflatex main.tex"}
{"ts":"...","session":"...","event":"spawn_agent","tool":"spawn_agent","input_summary":"review..."}
{"ts":"...","session":"...","event":"tool_failure","tool":"Bash","input_summary":"python train.py"}
{"ts":"...","session":"...","event":"slash_command","command":"/auto-review-loop","args":""}
{"ts":"...","session":"...","event":"user_prompt","prompt_preview":"change difficulty to hard"}
{"ts":"...","session":"...","event":"session_start","source":"startup","model":"claude-opus-4-6"}
{"ts":"...","session":"...","event":"session_end"}
```

## Triggering

This is a maintenance workflow, outside the normal research pipeline. Codex
installation supplies no automatic session logging or readiness callback. Import
explicit exports or use an authorized wrapper, inspect relevant complete tasks,
and run this skill when requested. Existing Claude hooks/check_ready reminders
apply only in a configured Claude installation; their invocation count does not
establish complete task coverage or scientific success.

After an actual optimization analysis, update existing optimization history with
the source coverage and resolved model. Do not invent a model from missing fields.

## Acknowledgements

Inspired by [Meta-Harness](https://arxiv.org/abs/2603.28052) (Lee et al., 2026) — end-to-end optimization of model harnesses via filesystem-based experience access and agentic code search.

## Output Protocols

> Follow these shared protocols for all output files:
> - **[Output Versioning Protocol](../shared-references/output-versioning.md)** — write timestamped file first, then copy to fixed name
> - **[Output Manifest Protocol](../shared-references/output-manifest.md)** — log every output to MANIFEST.md
> - **[Output Language Protocol](../shared-references/output-language.md)** — respect the project's language setting

## Review Tracing

After each reviewer agent call, save the trace following `shared-references/review-tracing.md` (Policy C — forensic; never silently skip). Use `save_trace.sh` (resolved per the chain in `shared-references/integration-contract.md` §2) or write files directly to `.ei/traces/<skill>/<date>_run<NN>/`. Respect the `--- trace:` parameter (default: `full`).
