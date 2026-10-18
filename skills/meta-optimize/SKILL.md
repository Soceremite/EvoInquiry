---
name: meta-optimize
description: "Analyze ARIS usage logs and propose optimizations to SKILL.md files, reviewer prompts, and workflow defaults. Outer-loop harness optimization inspired by Meta-Harness (Lee et al., 2026). Use when user says \"优化技能\", \"meta optimize\", \"improve skills\", \"分析使用记录\", or wants to optimize ARIS's own harness components based on accumulated experience."
argument-hint: "[target-skill-or-all]"
allowed-tools: Bash(*), Read, Grep, Glob, mcp__codex__codex, mcp__codex__codex-reply
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.
<!-- EVO-INQUIRY:END -->


<!-- EI-GOVERNANCE:BEGIN -->
Resolve runtime state through tools/state_paths.py before .ei operations. Use
[project-governance](../shared-references/project-governance.md) for fixed evidence,
profiles and controlled migration; missing profiles retain compat-v1.
<!-- EI-GOVERNANCE:END -->


# Meta-Optimize: Outer-Loop Harness Optimization for ARIS

Analyze accumulated usage logs and propose optimizations for: **$ARGUMENTS**

## Privilege boundary — this skill is a READ-ONLY PRODUCER

meta-optimize **proposes**; it does not **land**. The mutation of the skill corpus
is the exclusive job of a separate, human-invoked skill: [`/meta-apply`](../meta-apply/SKILL.md).
This split is structural, not advisory — it is why a missed instruction cannot let
this loop apply its own patch (the self-acquittal failure mode):

- **No `Write`/`Edit` tool.** This skill cannot edit a SKILL.md / shared-reference /
  any corpus file with the frictionless mutators. Its only outputs are the REPORT and
  staged patch files, written under `.ei/meta/` (a scratch area, never the corpus).
- **No apply step.** There is no in-skill "apply the patch" path (see Step 6). The
  producer ends by *staging* approved patches for `/meta-apply`; a human must then
  invoke `/meta-apply` to land them. That human action is the landing gate.
- **`Bash` writes to the corpus are filtered, not impossible — be honest about the
  layers.** What IS fully closed: the *accidental / in-flow* self-acquittal — this skill
  has no `Write`/`Edit` and no apply step, so an honest run cannot slip into editing the
  corpus. Defense-in-depth: install the
  [`corpus_write_guard`](../../templates/claude-hooks/corpus_write_guard.json) PreToolUse
  hook (like `meta_logging.json`), which DENIES the common Bash shell-writes (`>`, `tee`,
  `sed -i`, `cp`/`mv`, `touch`, `open(...,'w')`) to corpus paths. **This is a blacklist,
  NOT a complete sandbox** — a *deliberately* obscured Bash write (`git apply`, `patch`,
  `$var`/absolute paths, language file APIs) is not all caught. **Full structural
  prevention requires either removing this skill's `Bash` or an FS sandbox** — over-built
  for a not-yet-load-bearing producer, so deferred to when the gate carries real
  auto-modification volume (a brick-3 trigger). The intended backstop against a deliberate
  write is **detection, not prevention** — a corpus change with no valid/current
  `provenance` stamp (content-hash mismatch) *would be* catchable in a pre-push integrity
  check — but that verifier is **NOT yet built** (`provenance.py` has `content_hash` but no
  integrity-check subcommand, and no pre-push hook runs one). So today the deliberate-write
  case is neither prevented nor actively detected; track the integrity verifier as a
  follow-up before this producer goes load-bearing. Its legitimate Bash writes go only to
  `.ei/meta/`.

See [`shared-references/acceptance-gate.md`](../shared-references/acceptance-gate.md):
a loop can DRIVE (propose, review) same-model, but the ACQUITTAL that lands a change
must be cross-model (Step 4 jury) **and** the landing must be a separate human-gated
act (`/meta-apply`).

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

1. **Logging must be active.** Copy `templates/claude-hooks/meta_logging.json` into your project's `.claude/settings.json` (or merge the hooks section).
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
- Has the session model (`session_start` events' `model` field) or the pinned
  reviewer model changed since a skill's SKILL.md was last touched?
  (`git log -1 --format=%cs -- skills/<skill>/SKILL.md` vs the model-bump date.)
- A model bump is a **trigger to re-read, not evidence by itself**. For each
  reasoning-scaffolding step or worked example in that SKILL.md, a deletion
  proposal must cite TARGET-SPECIFIC evidence that the new model no longer
  needs it: a capability-specific release note, or repeated observed behavior
  in the event log (e.g. zero failures/interventions in the guarded step since
  the bump). "The model got newer" alone never justifies a deletion.
- **Never deletion candidates**, regardless of model: privilege boundaries,
  acceptance/review gates, corpus- and provenance-integrity rules, output
  contracts, and safety checks. The diet targets model-compensation scaffolding
  only — a capability the new model has natively is pure overhead (context
  weight, drift surface, reading cost). A harness that only ever grows is a
  harness nobody is re-reading.

**Trigger-rate analysis (optional, measured — not from the event log):**
- The event log shows which skills were USED, not which were WANTED-but-omitted
  — the omission failure mode (Claude Code passing over the right skill when the
  installed list is long) is invisible to it. `tools/meta_opt/trigger_eval.py`
  measures it directly: `claude -p` probes with paraphrased-intent queries run
  from a neutral cwd (so the realistic long installed corpus is loaded), scored
  as trigger / confusion(→which skill) / miss.
- Run it when a specific skill is suspected of under- or mis-triggering, or as a
  before/after check around a description edit:
  `python3 tools/meta_opt/trigger_eval.py --eval-file tools/meta_opt/trigger_evals.sample.json --skills <name> --samples 2`
- The **confusion matrix is the signal**, not just the rate: a query that keeps
  landing on a sibling skill means the two descriptions overlap on that intent —
  the fix is disambiguation, not "make the description pushier".
- **Measure-only, evidence not verdict.** A low trigger rate is an INPUT to a
  Step-2 proposal (which lands only via `/meta-apply`), never a self-applied
  description rewrite. Trigger rate is model-dependent, so compare like with
  like (record the probe model) and treat it as a proxy — it measures selection
  under a query set, not the full long-list omission problem.

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
quality", "experiment execution reliability", "writing polish" — with the
supporting evidence. The bottleneck always moves: when coding stops being the
constraint, planning becomes it; when planning is solved, verification; when
verification is automated, taste. This step exists to make the CURRENT
constraint visible, so Step 2's ranked table reads as sub-fixes for one named
constraint instead of scattered tweaks.

Append the verdict to the append-only ledger `.ei/meta/bottleneck_log.jsonl`
(same never-mutate discipline as `.ei/runs/<run_id>.iterations.jsonl`):

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

Never edit or delete prior lines — succession history is the point.

### Step 2: Identify Optimization Targets

Based on Step 1, rank optimization opportunities by expected impact:

```markdown
## Optimization Opportunities (ranked)

| # | Target | Signal | Proposed Change | Expected Impact |
|---|--------|--------|-----------------|-----------------|
| 1 | auto-review-loop default threshold | Users override to 7/10 in 60% of runs | Change default from 6/10 to 7/10 | Fewer manual overrides |
| 2 | experiment-bridge retry count | 40% of runs hit max retries on OOM | Add OOM-specific recovery (reduce batch size) | Fewer failed experiments |
| 3 | paper-write de-AI patterns | Users manually fix "delve" in 80% of runs | Add "delve" to default watchword list | Fewer manual edits |
| 4 | experiment-bridge Phase-2 hand-holding steps | Model bump (session_start model changed); scaffold untouched since 2 generations ago; zero tool_failures in the steps it guards | **DELETE steps N–M — the new model does this unprompted** | Smaller harness, less drift surface |
```

The Proposed-Change column is explicitly allowed to be a **deletion** — "DELETE
step N, new model does this for free" is a first-class optimization, ranked by
the same impact logic as additions.

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
- **Anti-self-poisoning screen** (see [`shared-references/capture-antipatterns.md`](../shared-references/capture-antipatterns.md)):
  run a proposed patch's rationale through `tools/capture_filter.py` (resolve via
  the canonical chain). NEVER propose a change that encodes a **negative
  tool-capability claim** ("codex can't…", "gemini is broken") or a **one-off /
  transient failure** as a durable rule — those harden into self-cited refusals.
  Encode the *fix / the flag needed / the workaround*, not "X can't do Y".

### Step 4: Cross-Model Review of Patches (ADVISORY pre-screen)

> This review is **advisory** — it sharpens the Step-5 REPORT so the human can decide
> what to stage. It is **not** the landing verdict. The binding cross-model jury runs
> later, at landing, inside [`/meta-apply`](../meta-apply/SKILL.md), on the actual staged
> diff (a producer-relayed verdict would be forgeable). Record this result as
> `advisory_screen` only.

Send each patch to GPT-6-Astra xhigh for adversarial review:

```
mcp__codex__codex:
  model: gpt-6-astra
  config: {"model_reasoning_effort": "xhigh"}
  prompt: |
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
This skill only **proposes**. To land changes: tell me which to stage, then run
`/meta-apply` (a separate, human-invoked applier that re-checks the cross-model
verdict before mutating anything). meta-optimize never applies.
```

### Step 6: Stage approved patches for `/meta-apply` (NO in-skill apply)

This skill does **not** apply anything. After the user has read the Step-5 REPORT and
indicated which changes to land, **stage** them for the privileged applier:

1. For each approved change `N`, write its unified diff to
   `.ei/meta/pending/<NN>_<skill>.diff` and append a row to
   `.ei/meta/pending/manifest.jsonl`:
   `{patch: "<NN>_<skill>.diff", target: "<corpus path>", author_model: "<executor>",
   advisory_screen: "pass|kill", advisory_reason: "<one line>"}`.
   The `advisory_screen` (your Step-4 codex pre-review) is **advisory only** — it helps
   the human read the REPORT. It is **NOT** the landing verdict and `/meta-apply` does not
   trust it: a producer-written verdict would be forgeable. The binding cross-model jury
   runs **at landing, inside `/meta-apply`,** on the actual staged diff.
2. Tell the user: *"Staged M patches. Run `/meta-apply` to judge & land them."*

The backup → **fresh jury-at-landing** → apply → **provenance stamp** → log all happen
inside [`/meta-apply`](../meta-apply/SKILL.md). meta-optimize never touches the corpus and
never produces the acquittal.

**Never apply in this skill. Landing is `/meta-apply` + a fresh jury + a human, always.**

## Key Rules

- **Log-driven, not speculative.** Every proposed change must cite specific data from the event log. No "I think this would be better."
- **Minimal patches.** Change one thing at a time. Don't rewrite entire skills — the one sanctioned large edit is a scaffolding **deletion** backed by TARGET-SPECIFIC model-delta evidence (a capability-specific release note, or repeated post-bump event-log behavior showing the scaffold is unused — the model name changing is a trigger to look, never sufficient evidence). Privilege boundaries, acceptance gates, corpus/provenance rules, output contracts, and safety checks are never deletion candidates. Deletions go through the same review + approval gates as everything else.
- **Reviewer-gated.** Every patch goes through cross-model review before recommendation.
- **Reversible.** Always back up before applying. Always log what changed.
- **User-approved.** Never auto-apply. Present, explain, let the user decide.
- **Honest about uncertainty.** If the data is insufficient, say so. Don't optimize on noise.
- **Portable.** Optimizations should improve the skill for all users, not just one user's style. If a change seems user-specific, flag it.

## Event Schema Reference

The log at `.ei/meta/events.jsonl` contains JSONL records with these shapes:

```jsonl
{"ts":"...","session":"...","event":"skill_invoke","skill":"auto-review-loop","args":"difficulty: hard"}
{"ts":"...","session":"...","event":"PostToolUse","tool":"Bash","input_summary":"pdflatex main.tex"}
{"ts":"...","session":"...","event":"codex_call","tool":"mcp__codex__codex","input_summary":"review..."}
{"ts":"...","session":"...","event":"tool_failure","tool":"Bash","input_summary":"python train.py"}
{"ts":"...","session":"...","event":"slash_command","command":"/auto-review-loop","args":""}
{"ts":"...","session":"...","event":"user_prompt","prompt_preview":"change difficulty to hard"}
{"ts":"...","session":"...","event":"session_start","source":"startup","model":"claude-opus-4-6"}
{"ts":"...","session":"...","event":"session_end"}
```

## Triggering

This skill is NOT part of the standard W1→W1.5→W2→W3→W4 pipeline. It is a **maintenance workflow** with three trigger mechanisms:

1. **Passive logging** (when the hooks are configured): Claude Code hooks record events to `.ei/meta/events.jsonl` automatically during normal usage. Zero user effort.

2. **Automatic readiness check** (SessionEnd hook): When a Claude Code session ends, `check_ready.sh` counts skill invocations since the last `/meta-optimize` run. If ≥5 new invocations have accumulated, it prints a reminder:
   ```
   📊 ARIS has logged 8 skill runs since last optimization. Run /meta-optimize to check for improvement opportunities.
   ```
   It ALSO fires — regardless of invocation count — when the session model has
   changed since the last optimize (compared against `.ei/meta/.last_optimize_model`):
   ```
   🔁 Model changed since last optimization (claude-opus-4-6 → claude-opus-4-8). Run /meta-optimize — a model bump makes existing scaffolding a deletion candidate (harness diet).
   ```
   Both are **suggestions only** — they do not auto-run optimization.

3. **Manual trigger**: User runs `/meta-optimize` when they see the reminder or whenever they want.

**After each `/meta-optimize` run**, the skill writes the current timestamp to `.ei/meta/.last_optimize` and the current session model (latest `session_start` event's `model` field) to `.ei/meta/.last_optimize_model`, so the readiness check can detect both new usage and model bumps.

## Acknowledgements

Inspired by [Meta-Harness](https://arxiv.org/abs/2603.28052) (Lee et al., 2026) — end-to-end optimization of model harnesses via filesystem-based experience access and agentic code search.

## Output Protocols

> Follow these shared protocols for all output files:
> - **[Output Versioning Protocol](../shared-references/output-versioning.md)** — write timestamped file first, then copy to fixed name
> - **[Output Manifest Protocol](../shared-references/output-manifest.md)** — log every output to MANIFEST.md
> - **[Output Language Protocol](../shared-references/output-language.md)** — respect the project's language setting

## Review Tracing

After each `mcp__codex__codex` or `mcp__codex__codex-reply` reviewer call, save the trace following `shared-references/review-tracing.md` (Policy C — forensic; never silently skip). Use `save_trace.sh` (resolved per the chain in `shared-references/integration-contract.md` §2) or write files directly to `.ei/traces/<skill>/<date>_run<NN>/`. Respect the `--- trace:` parameter (default: `full`).
