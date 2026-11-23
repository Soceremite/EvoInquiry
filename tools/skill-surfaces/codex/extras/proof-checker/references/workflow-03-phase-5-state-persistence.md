<!-- EI-WORKFLOW-REFERENCE -->

# Phase 5: State Persistence

Read this file when the workflow reaches Phase 5: State Persistence through Example Invocations. In commands and examples, interpret relative skill paths from the entrypoint directory.

### Phase 5: State Persistence

Write `PROOF_CHECK_STATE.json`:
```json
{
  "status": "completed",
  "rounds": 2,
  "review_agent_ids": ["..."],
  "fatal_fixed": 0,
  "critical_fixed": 3,
  "major_fixed": 2,
  "minor_fixed": 1,
  "counterexamples_found": 1,
  "counterexample_candidates": 2,
  "acceptance_gate": "PASS",
  "timestamp": "..."
}
```

### Phase 5.5: Research Wiki Claim Ledger (additive; only if a wiki is active)

If — and only if — a `research-wiki/` exists, persist each top-level theorem/headline
as a **claim node** (the wiki's PROVE/JUDGE ledger). This is the **birth point** for wiki
claim nodes. It is a **detect-only record, never a verdict**: it never changes the audit's
`verdict`/`reason_code`, never blocks, and is skipped when `verdict == NOT_APPLICABLE` or no
wiki is found. The claim's `status` is the **PROOF axis only** ({drafted, unproven,
sound-modulo-imports, verified, refuted, retracted}); empirical experiment support is a
separate axis carried by edges (`/result-to-claim`), never written into `status`.

Resolve the helper via the Codex-side chain (skip cleanly if unavailable; the audit is
already complete):
```
ARIS_REPO="${ARIS_REPO:-$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills-codex.txt 2>/dev/null)}"
WIKI_SCRIPT=""
[ -n "$ARIS_REPO" ] && [ -f "$ARIS_REPO/tools/research_wiki.py" ] && WIKI_SCRIPT="$ARIS_REPO/tools/research_wiki.py"
[ -z "$WIKI_SCRIPT" ] && [ -f tools/research_wiki.py ] && WIKI_SCRIPT="tools/research_wiki.py"
[ -z "$WIKI_SCRIPT" ] && [ -f ~/.codex/skills/research-wiki/research_wiki.py ] && WIKI_SCRIPT="$HOME/.codex/skills/research-wiki/research_wiki.py"
```

If `research-wiki/` exists and `WIKI_SCRIPT` is available and `verdict != NOT_APPLICABLE`,
for each top-level theorem map the audit outcome to an honest status — `PASS`/all proofs
complete → `verified`; closes modulo flagged imports → `sound-modulo-imports`; counterexample
found or statement judged false → `refuted`; open gap (UNJUSTIFIED, no counterexample) →
`unproven` (never fake a gap as `refuted`/`verified`) — then record it (idempotent):
```
python3 "$WIKI_SCRIPT" add_claim research-wiki/ --slug "<stable-theorem-id>" \
     --name "<theorem headline>" --status "<mapped status>" \
     --provenance "<trace_path from PROOF_AUDIT.json>" --statement "<canonical statement>" \
     --scope "<what it does NOT say; flagged imports>" --update-on-exist
```
`add_claim` failure is non-fatal (warn and continue; the audit is unaffected).

## Key Rules

### Mathematical rigor
- **Never accept a proof step on faith**. "Clearly" / "it follows" / "by standard arguments" are red flags — each must spawn a micro-claim.
- **Hypothesis discharge**: Every time a lemma is APPLIED, verify EACH of its hypotheses at that point. Use the side-condition checklists above.
- **Interchange discipline**: Every swap of limit/expectation/derivative/integral must cite a theorem (DCT/MCT/Fubini/Leibniz) and verify its conditions with explicit dominating function or integrability proof.
- **Uniformity discipline**: Every O(·)/Θ(·) must declare what parameters it is uniform over. "O(1)" that secretly depends on d,n,K is a CONSTANT_DEPENDENCE_HIDDEN issue.
- **Quantifier discipline**: Check ∀/∃ order. "For sufficiently small κ" must specify: does κ₀ depend on K? On π? On d?
- **Counterexample-first**: Before trying to fix a gap, first try to break it.
- **WLOG prohibition**: Every "without loss of generality" must have an explicit micro-claim proving the reduction. No free WLOGs.
- **No silent assumption strengthening**: Any fix that adds conditions must propagate to the theorem statement.

### Review-independence protocol
- **Codex executor analyzes and implements; a fresh Codex reviewer provides adversarial review.** Base review remains same-family/provisional.
- **Codex reasoning always ultra** (deep-audit tier): never below `xhigh` — only the capability fallback in `reviewer-routing.md` may step down, and only on explicit capability errors.
- **Send full content**: Don't summarize — send actual math for line-by-line checking.
- **Fresh reviewer agents**: Save each returned `agent_id` for traceability, but launch a new `spawn_agent` for each review round. Do not use `send_input` across proof-checker rounds.

### Fix quality
- **Minimal fixes**: Fix exactly what's broken, nothing more.
- **Full derivation**: Every fix includes complete mathematical argument.
- **Explicit scope decisions**: Each fix is tagged ADD_DERIVATION / STRENGTHEN_ASSUMPTION / WEAKEN_CLAIM / ADD_REFERENCE.
- **Compile after each fix**: LaTeX must compile cleanly.

### Scope honesty
- **Don't overclaim**: If a fix makes a result conditional, say so.
- **Separate "proven" from "assumed"**: The audit report has an explicit section for this.
- **Log open problems**: Issues requiring future work are listed, not hidden.

## Output Files

| File | Content | When |
|------|---------|------|
| `PROOF_SKELETON.md` | Dependency DAG + assumption ledger + micro-claims | Phase 0.5 |
| `PROOF_AUDIT.md` | Cumulative round-by-round audit log | Updated each round |
| `PROOF_AUDIT.json` | Machine-readable submission verdict (see below) | Always emitted |
| `proof_audit_report.tex/.pdf` | Formal before/after report | Phase 4 |
| `PROOF_CHECK_STATE.json` | State for recovery | Phase 5 |
| `PROOF_AUDIT.html` (+ `.review.json` sidecar) | Single-file HTML view auto-rendered via `/render-html "PROOF_AUDIT.md" --json "PROOF_AUDIT.json"`. **Non-blocking** — if `/render-html` fails the audit still counts as complete. | Workflow end (when `RENDER_HTML = true`, default) |

## Submission Artifact Emission

This skill **always** writes `PROOF_AUDIT.json` at the paper directory
root (i.e. `paper/PROOF_AUDIT.json` when invoked from `/paper-writing`
with paper-dir `paper/`; `<your-paper-dir>/PROOF_AUDIT.json` when invoked
standalone), regardless of caller or whether the paper contains theorems.
A paper with no `\begin{theorem}` / `\begin{lemma}` / `\begin{proof}` emits
verdict `NOT_APPLICABLE`; silent skip is forbidden. `paper-writing`
Phase 6 and `verify_paper_audits.sh` both rely on this artifact
existing at `<paper-dir>/PROOF_AUDIT.json`.

The artifact conforms to the schema in `shared-references/assurance-contract.md`:

```json
{
  "audit_skill":      "proof-checker",
  "verdict":          "PASS | WARN | FAIL | NOT_APPLICABLE | BLOCKED | ERROR",
  "reason_code":      "all_proofs_complete | minor_gaps | critical_gap | no_theorems | ...",
  "summary":          "One-line human-readable verdict summary.",
  "audited_input_hashes": {
    "main.tex":                 "sha256:...",
    "sections/4.theory.tex":    "sha256:..."
  },
  "trace_path":       ".ei/traces/proof-checker/<date>_run<NN>/",
  "thread_id":        "<codex mcp thread id>",
  "executor_model":   "codex-gpt-6-astra",
  "executor_family":  "openai",
  "reviewer_model":   "gpt-6-astra",
  "reviewer_family":  "openai",
  "review_independence": "same-family",
  "acceptance_status": "provisional",
  "reviewer_reasoning": "ultra",
  "generated_at":     "<UTC ISO-8601>",
  "details": {
    "theorems_audited": <int>,
    "issues": [ { "id": "T1-H3", "severity": "FATAL|CRITICAL|MAJOR|MINOR",
                  "category": "quantifier|domination|...",
                  "location": "sections/4.theory.tex:L182",
                  "note": "..." }, ... ]
  }
}
```

### `audited_input_hashes` scope

Hash the **declared input set** actually reviewed — the theorem-bearing
`.tex` files passed into this invocation — not a repo-wide union and not
the reviewer's self-reported opened subset. The external verifier rehashes
these entries; any mismatch flags `STALE`.

**Path convention** (must match `verify_paper_audits.sh`): keys are
**paths relative to the paper directory** (no `paper/` prefix — the
verifier resolves relative to the paper dir; prefixing produces
`paper/paper/...` and false-fails as STALE). Use **absolute paths** for
files outside the paper dir.

### Verdict decision table

| Input state                                           | Verdict          | `reason_code` example |
|-------------------------------------------------------|------------------|-----------------------|
| No theorems / lemmas / proofs in paper                | `NOT_APPLICABLE` | `no_theorems`         |
| Theorems present but referenced files unreadable      | `BLOCKED`        | `source_unreadable`   |
| All proof obligations discharged, no gaps             | `PASS`           | `all_proofs_complete` |
| Only MINOR issues (notation / exposition)             | `WARN`           | `minor_gaps`          |
| Any FATAL or CRITICAL issue (logic gap, wrong claim)  | `FAIL`           | `critical_gap`        |
| Reviewer invocation failed (network / malformed)      | `ERROR`          | `reviewer_error`      |

MAJOR issues alone map to `WARN` or `FAIL` at the reviewer's discretion and
must carry an explicit justification in `summary` + `details.issues`.

### Thread independence

Every invocation uses a fresh reviewer agent. Never use `send_input` across
proof-checker runs. Do not accept prior audit outputs
(PAPER_CLAIM_AUDIT, CITATION_AUDIT, EXPERIMENT_LOG) as input — the fresh
thread preserves reviewer independence per
`shared-references/reviewer-independence.md`.

This skill never blocks by itself; `paper-writing` Phase 6 plus the
verifier decide whether the verdict blocks finalization based on the
`assurance` level.

## Example Invocations

```
/proof-checker "neurips_2025.tex"
/proof-checker "check the GMM generalization proof, focus on dimension dependence"
/proof-checker "verify proof in paper.tex — difficulty: nightmare"
```
