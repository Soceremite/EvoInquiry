---
name: result-to-claim
description: "Assess whether completed experiments support a specified research claim, with evidence checks and fresh review. Use for requested claim verdicts or required workflow gates."
argument-hint: "[experiment-description-or-wandb-run]"
allowed-tools: Bash(*), Read, Grep, Glob, Write, Edit
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.

Apply this formal gate when a claim-support verdict is requested or the active workflow requires it; ordinary analysis caveats alone do not trigger it. See [task-scope](../shared-references/task-scope.md). When required, all existing evidence, review, and routing rules below still apply.

For this stage, read [project-governance](../shared-references/project-governance.md). Use fixed raw result/spec/execution/report refs and the actual digest-bound review receipt. Preserve independent/provisional judgments; file/registry/schema success does not establish claim support.
For comparative claims, load [comparative-experiments](../shared-references/comparative-experiments.md) into the existing review brief. Match the claim to a controlled, resource-bound or tuned-system comparison; assess leakage, selection, seed/failure coverage and uncertainty from fixed raw evidence. Explain confounds and narrow unsupported conclusions. Keep the existing review gates and do not turn an ordinary analysis into an unsolicited formal verdict.
Use the discovered runtime entrypoint; in Codex this is
skills/skills-codex/result-to-claim/SKILL.md. Read the evidence-precheck input
contract before constructing a batch. An unavailable reviewer does not prevent
saving the requested preliminary assessment and evidence limits; keep the
independent verdict pending and the required review gate BLOCKED. Do not invent
a reviewer response or advance from the executor's own interpretation.
<!-- EVO-INQUIRY:END -->


# Result-to-Claim Gate

> **Codex assurance:** deterministic evidence existence can be accepted, while
> the base semantic claim judgment records `review_independence: same-family`
> and `acceptance_status: provisional`. Cross-family overlays may record
> accepted; reviewer failure emits BLOCKED.

Experiments produce numbers; this gate decides what those numbers *mean*. Collect results from available sources, get a secondary Codex judgment, then auto-route based on the verdict.

## Context: $ARGUMENTS

## When to Use

- After a set of experiments completes (main results, not just sanity checks)
- Before committing to claims in a paper or review response
- When results are ambiguous and you need an objective second opinion

## Evidence calibration

Keep `claim_supported: yes | partial | no` and existing review gates. Explain
whether an unsupported claim has contrary evidence or simply lacks sufficient
evidence; `no` is not automatically a refutation. File existence, number matching,
review acceptance and scientific support are distinct judgments. Preserve gains,
regressions, unknowns and the original primary metric in the reviewer brief.

## Workflow

### Step 1: Collect Results

Gather experiment data from whatever sources are available in the project:

1. **W&B** (preferred): `wandb.Api().run("<entity>/<project>/<run_id>").history()` — metrics, training curves, comparisons
2. **EXPERIMENT_LOG.md**: full results table with baselines and verdicts
3. **EXPERIMENT_TRACKER.md**: check which experiments are DONE vs still running
4. **Log files**: `ssh server "tail -100 /path/to/training.log"` if no other source
5. **`idea-stage/docs/research_contract.md`** (legacy fallback: `docs/research_contract.md`): intended claims and experiment design

Assemble the key information:
- What experiments were run (method, dataset, config)
- Main metrics and baseline comparisons (deltas)
- The intended claim these experiments were designed to test
- Any known confounds or caveats

### Step 1.5: Deterministic evidence pre-check

Before the reviewer call, resolve and run `evidence_check.py` per
[`evidence-precheck.md`](../shared-references/evidence-precheck.md):

```bash
if [ -z "${ARIS_REPO:-}" ] && [ -f .ei/installed-skills-codex.txt ]; then
  ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills-codex.txt 2>/dev/null) || true
fi
EVIDENCE_CHECK=""
[ -n "${ARIS_REPO:-}" ] && [ -f "$ARIS_REPO/tools/evidence_check.py" ] && EVIDENCE_CHECK="$ARIS_REPO/tools/evidence_check.py"
[ -z "$EVIDENCE_CHECK" ] && [ -f tools/evidence_check.py ] && EVIDENCE_CHECK="tools/evidence_check.py"
mkdir -p .ei
if [ -n "$EVIDENCE_CHECK" ]; then
  python3 "$EVIDENCE_CHECK" . --batch .ei/claims.json \
    > .ei/evidence_precheck.json 2>.ei/evidence_precheck.err || true
else
  echo "WARN: evidence_check.py unresolved; semantic review will still run" >&2
fi
```

Treat `path_missing` and `value_not_found` as unsupported evidence before the
semantic review. `verified` means only that the cited value exists; it does not
prove the claim. Pass the pre-check JSON path to the fresh reviewer. The Codex
reviewer's positive result remains `review_independence: same-family` and
`acceptance_status: provisional`; a deterministic evidence check never upgrades
a semantic claim to accepted by itself.

### Step 2: Codex Judgment

Send the collected results to a secondary Codex agent for objective evaluation:

```text
spawn_agent:
  model: gpt-6-astra
  reasoning_effort: ultra
  message: |
    RESULT-TO-CLAIM EVALUATION

    I need you to judge whether experimental results support the intended claim.

    Intended claim: [the claim these experiments test]

    Experiments run:
    [list experiments with method, dataset, metrics]

    Results:
    [paste key numbers, comparison deltas, significance]

    Baselines:
    [baseline numbers and sources — reproduced or from paper]

    Known caveats:
    [any confounding factors, limited datasets, missing comparisons]

    Please evaluate:
    1. claim_supported: yes | partial | no
    2. what_results_support: what the data actually shows
    3. what_results_dont_support: where the data falls short of the claim
    4. missing_evidence: specific evidence gaps
    5. suggested_claim_revision: if the claim should be strengthened, weakened, or reframed
    6. next_experiments_needed: specific experiments to fill gaps (if any)
    7. confidence: high | medium | low

    Be honest. Do not inflate claims beyond what the data supports.
    A single positive result on one dataset does not support a general claim.
```

### Step 3: Parse and Normalize

Extract structured fields from the secondary Codex response:

```markdown
- claim_supported: yes | partial | no
- what_results_support: "..."
- what_results_dont_support: "..."
- missing_evidence: "..."
- suggested_claim_revision: "..."
- next_experiments_needed: "..."
- confidence: high | medium | low
```

### Step 3.5: Check Experiment Integrity (if audit exists)

**Skip this step if `EXPERIMENT_AUDIT.json` does not exist.**

```
if EXPERIMENT_AUDIT.json exists:
    read integrity_status from file
    attach to verdict output:
        integrity_status: pass | warn | fail

    if integrity_status == "fail":
        append to verdict: "[INTEGRITY CONCERN] — audit found issues, see EXPERIMENT_AUDIT.md"
        downgrade confidence to "low" regardless of Codex judgment

    if integrity_status == "warn":
        append to verdict: "[INTEGRITY: WARN] — audit flagged potential issues"
else:
    integrity_status = "unavailable"
    verdict is labeled "provisional — no integrity audit run"
    (this does NOT block anything — pipeline continues normally)
```

See `shared-references/experiment-integrity.md` for the full integrity protocol.

### Step 4: Route Based on Verdict

#### `no` — Claim not supported

1. Record postmortem in findings.md (Research Findings section):
   - What was tested, what failed, hypotheses for why
   - Constraints for future attempts (what NOT to try again)
2. Update the project pipeline status in `AGENTS.md` or project notes
3. Decide whether to pivot to next idea from IDEA_CANDIDATES.md or try an alternative approach

#### `partial` — Claim partially supported

1. Update the working claim to reflect what IS supported
2. Record the gap in findings.md
3. Design and run supplementary experiments to fill evidence gaps
4. Re-run result-to-claim after supplementary experiments complete
5. **Multiple rounds of `partial` on the same claim** → record analysis in findings.md, consider whether to narrow the claim scope or switch ideas

#### `yes` — Claim supported

1. Record confirmed claim in project notes
2. If ablation studies are incomplete → trigger `/ablation-planner`
3. If all evidence is in → ready for paper writing

### Step 5: Update Research Wiki (if active)

**Skip this step entirely if `research-wiki/` does not exist.**

```
if research-wiki/ exists:
    # Resolve the helper (Codex chain). If unavailable, skip wiki writes; still report verdict.
    ARIS_REPO="${ARIS_REPO:-$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills-codex.txt 2>/dev/null)}"
    WIKI_SCRIPT=""
    [ -n "$ARIS_REPO" ] && [ -f "$ARIS_REPO/tools/research_wiki.py" ] && WIKI_SCRIPT="$ARIS_REPO/tools/research_wiki.py"
    [ -z "$WIKI_SCRIPT" ] && [ -f tools/research_wiki.py ] && WIKI_SCRIPT="tools/research_wiki.py"
    [ -z "$WIKI_SCRIPT" ] && [ -f ~/.codex/skills/research-wiki/research_wiki.py ] && WIKI_SCRIPT="$HOME/.codex/skills/research-wiki/research_wiki.py"
    [ -n "$WIKI_SCRIPT" ] || echo "WARN: research_wiki.py unreachable; skipping wiki writes (verdict still reported)." >&2

    # 1. Create/refresh the experiment node FIRST (verdict OWNER → --update-on-exist so a
    #    re-judge overwrites the stale verdict). The supports/invalidates edges in #2 point
    #    FROM exp:<id> and add_edge does NOT verify node existence, so only add them if the
    #    experiment node was born (EXP_NODE_OK); otherwise skip the wiki edges.
    EXP_NODE_OK=0
    [ -n "$WIKI_SCRIPT" ] && python3 "$WIKI_SCRIPT" add_experiment research-wiki/ \
         --slug "<exp_id>" --idea "idea:<active_idea>" \
         --verdict "<yes|partial|no>" --confidence "<high|medium|low>" \
         --date "<date>" --hardware "<hw>" --duration "<dur>" \
         --metrics "<key metrics>" --reasoning "<one-line why this verdict>" \
         --provenance "<EXPERIMENT_AUDIT.md / run dir>" --update-on-exist && EXP_NODE_OK=1

    # 2. Record empirical support as EDGES ONLY, and ONLY if EXP_NODE_OK. NEVER edit a
    #    claim page's `status`: that is the PROOF axis (verified / refuted / unproven /
    #    sound-modulo-imports / drafted / retracted), owned by /proof-checker (the claim
    #    birth point) — the ARIS helper REJECTS "supported"/"partial"/"invalidated".
    if [ "$EXP_NODE_OK" = 1 ]:
        for each claim resolved by this verdict:
            if verdict == "yes":
                python3 "$WIKI_SCRIPT" add_edge research-wiki/ --from "exp:<id>" --to "claim:<cid>" --type supports --evidence "<metric>"
            elif verdict == "partial":
                python3 "$WIKI_SCRIPT" add_edge research-wiki/ --from "exp:<id>" --to "claim:<cid>" --type supports --evidence "partial: <metric>"
            else:
                python3 "$WIKI_SCRIPT" add_edge research-wiki/ --from "exp:<id>" --to "claim:<cid>" --type invalidates --evidence "<why>"

    # 3. Update idea outcome (raw markdown, helper-free — preserves the rich idea body)
    Update research-wiki/ideas/<idea_id>.md:
      - outcome: positive | mixed | negative
      - If negative: fill "Failure / Risk Notes" and "Lessons Learned"
      - If positive: fill "Actual Outcome" and "Reusable Components"

    # 4. Rebuild + log (reflect the new edges; only if WIKI_SCRIPT resolved)
    [ -n "$WIKI_SCRIPT" ] && python3 "$WIKI_SCRIPT" rebuild_query_pack research-wiki/
    [ -n "$WIKI_SCRIPT" ] && python3 "$WIKI_SCRIPT" log research-wiki/ "result-to-claim: exp:<id> verdict=<verdict> for idea:<idea_id>"

    # 5. Re-ideation suggestion
    Count failed/partial ideas since last /idea-creator run.
    If >= 3: print "💡 3+ ideas tested since last ideation. Consider re-running /idea-creator — the wiki now knows what doesn't work."
```

## Rules

- **The secondary Codex agent is the judge, not the local executor.** The local executor collects evidence and routes; the reviewer agent evaluates. This prevents post-hoc rationalization.
- Do not inflate claims beyond what the data supports. If Codex says "partial", do not round up to "yes".
- A single positive result on one dataset does not support a general claim. Be honest about scope.
- If `confidence` is low, treat the judgment as inconclusive and add experiments rather than committing to a claim.
- **Fail closed if the reviewer is unavailable.** Follow the capability fallback
  in `reviewer-routing.md` (`gpt-6-astra` + `ultra` → `gpt-6-astra` + `xhigh`
  → `gpt-5.5` + `xhigh`), and never downgrade on timeout, rate-limit, auth,
  transport, server, or context errors. If no allowed pair succeeds, write a
  traced `BLOCKED` review record with the unavailable route and evidence paths, write
  `CLAIMS_FROM_RESULTS.md` containing only `verdict: REVIEW_UNAVAILABLE`, record
  the same in findings.md, and stop. Do not emit a local PASS/WARN substitute or
  advance a submission-facing claim; only an explicitly non-submission
  evidence-gathering phase may continue.
- Always record the verdict and reasoning in findings.md, regardless of outcome.

## Review Tracing

After the secondary Codex judgment, save a trace following `../shared-references/review-tracing.md`. Write files directly to `.ei/traces/result-to-claim/<date>_run<NN>/` and include the prompt, raw reviewer response, parsed verdict, routing action, and whether the result is `[pending external review]`. Respect the `--- trace:` parameter when present (default: `full`).
