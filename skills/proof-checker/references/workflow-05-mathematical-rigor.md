<!-- EI-WORKFLOW-REFERENCE -->

# Mathematical rigor

Read this file when the workflow reaches Mathematical rigor through Verdict decision table. In commands and examples, interpret relative skill paths from the entrypoint directory.

### Mathematical rigor
- **Never accept a proof step on faith**. "Clearly" / "it follows" / "by standard arguments" are red flags — each must spawn a micro-claim.
- **Hypothesis discharge**: Every time a lemma is APPLIED, verify EACH of its hypotheses at that point. Use the side-condition checklists above.
- **Interchange discipline**: Every swap of limit/expectation/derivative/integral must cite a theorem (DCT/MCT/Fubini/Leibniz) and verify its conditions with explicit dominating function or integrability proof.
- **Uniformity discipline**: Every O(·)/Θ(·) must declare what parameters it is uniform over. "O(1)" that secretly depends on d,n,K is a CONSTANT_DEPENDENCE_HIDDEN issue.
- **Quantifier discipline**: Check ∀/∃ order. "For sufficiently small κ" must specify: does κ₀ depend on K? On π? On d?
- **Counterexample-first**: Before trying to fix a gap, first try to break it.
- **WLOG prohibition**: Every "without loss of generality" must have an explicit micro-claim proving the reduction. No free WLOGs.
- **No silent assumption strengthening**: Any fix that adds conditions must propagate to the theorem statement.

### Cross-model protocol
- **Executor analyzes, reviewer critiques**: Claude reads proof, formulates questions, implements fixes. The external reviewer provides adversarial review.
- **Reviewer reasoning always ultra** (deep-audit tier): never below `xhigh` — only the capability fallback chain in `reviewer-routing.md` may step down, and only on explicit capability errors.
- **Send full content**: Don't summarize — send actual math for line-by-line checking.
- **Preserve threadId within a single run**: Use the appropriate reply tool (`mcp__codex__codex-reply` or `mcp__manual_review__review_reply`) for Phase 3 follow-up rounds within the same top-level `/proof-checker` invocation, so the reviewer keeps prior-issue context when judging whether a fix closed the gap. Across separate top-level invocations, always start a fresh thread (see "Thread independence" below).

### Fix quality
- **Minimal fixes**: Fix exactly what's broken, nothing more.
- **Full derivation**: Every fix includes complete mathematical argument.
- **Explicit scope decisions**: Each fix is tagged ADD_DERIVATION / STRENGTHEN_ASSUMPTION / WEAKEN_CLAIM / ADD_REFERENCE.
- **Compile after each fix**: LaTeX must compile cleanly.

### Scope honesty
- **Don't overclaim**: If a fix makes a result conditional, say so.
- **Separate "proven" from "assumed"**: The audit report has an explicit section for this.
- **Log open problems**: Issues requiring future work are listed, not hidden.

### Opt-in flag discipline
- **Deep-fix is opt-in only**: never auto-enable; never block on `deep_fix_plans` content; existing callers must observe identical reviewer output and identical JSON schema if they do not pass `--deep-fix`.
- **Reviewer prompt augmentation is additive**: the deep-fix block is appended to the Phase 1 prompt, not substituted for any part of it. The original mandatory checklist (A-H) and original per-issue OUTPUT FORMAT remain in place verbatim.
- **Restatement check is opt-in only**: Phase 3.6 runs only when `--restatement-check` is set; existing callers must observe identical reviewer output and identical JSON schema if they do not pass the flag.
- **No Phase reordering**: enabling Phase 3.6 inserts it strictly between 3.5 and 3.9; it does not skip any other phase or change their semantics.
- **No verdict crosstalk**: neither deep-fix output nor `restatement_drift` ever alters top-level `verdict` or `reason_code`. A paper with non-empty drift or with deep-fix plans may still pass; a paper with FAIL verdict stays FAIL whether or not either flag was set.

## Output Files

| File | Content | When |
|------|---------|------|
| `PROOF_SKELETON.md` | Dependency DAG + assumption ledger + micro-claims | Phase 0.5 |
| `PROOF_AUDIT.md` | Cumulative round-by-round audit log | Updated each round |
| `PROOF_AUDIT.json` | Machine-readable submission verdict (see below) | Always emitted |
| `proof_audit_report.tex/.pdf` | Formal before/after report | Phase 4 |
| `PROOF_CHECK_STATE.json` | State for recovery | Phase 5 |
| `PROOF_AUDIT.html` (+ `.review.json` sidecar) | Single-file HTML view of `PROOF_AUDIT.md` auto-rendered via `/render-html "PROOF_AUDIT.md" --json "PROOF_AUDIT.json"`. **Non-blocking** — if `/render-html` fails the audit still counts as complete; `PROOF_AUDIT.{md,json}` are the canonical outputs. | Workflow end (when `RENDER_HTML = true`, default) |

When `--restatement-check` is set, `PROOF_AUDIT.json` additionally carries `details.restatement_drift` and `details.restatement_check_status`; both fields are omitted when the flag is unset. See "Submission Artifact Emission" below.

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
  "reviewer_model":   "<resolved — the model that actually ran (target: gpt-6-astra)>",
  "reviewer_reasoning": "<resolved — the effort that actually ran (target: ultra)>",
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

### Optional: `details.deep_fix_plans` (only when `--deep-fix` is set)

```json
"details": {
  ...
  "deep_fix_plans": [
    {
      "issue_id": "T1-H3",
      "corrected_statement": "<LaTeX, paste-ready>",
      "changed_equations": [{"before": "<LaTeX>", "after": "<LaTeX>"}, ...],
      "downstream_labels": ["thm:convergence", "cor:minimax", ...],
      "minimal_tex_patch_plan": [
        {"file": "sections/4.theory.tex",
         "anchor_old": "<unique LaTeX snippet>",
         "replacement_new": "<LaTeX to insert>"},
        ...
      ],
      "closure_tests": [
        "verify constant_dependence_diff matches computed value",
        "limit case γ→0 reduces to identity",
        ...
      ],
      "algebra_sanity": {
        "dimension_table": {"<symbol>": "<type_signature>", ...},
        "power_count": "<one-line check>",
        "zero_coupling_check": "<one-line check>",
        "constant_dependence_diff": "<before vs after>"
      }
    }
  ],
  "deep_fix_status": "ok" | "unavailable"
}
```

Field semantics:
- Both `deep_fix_plans` and `deep_fix_status` are **omitted entirely** when the flag is not set. The default schema does not include either key.
- When the flag is set and reviewer returns well-formed plans, `deep_fix_status` is `"ok"` and `deep_fix_plans` mirrors `details.issues` one-to-one (each plan referenced by `issue_id`); `algebra_sanity` is present only for issues invoking Schur / Young / Cauchy-Schwarz / Hölder / quadratic-form / operator-norm / power-counting steps.
- When the flag is set but reviewer output is malformed or truncated, `deep_fix_status` is `"unavailable"` and `deep_fix_plans` is `[]`. Downstream consumers MUST treat `"unavailable"` identically to the field being absent: not blocking.
- Downstream consumers MUST treat absence of either field as the only valid default state and MUST NOT raise on missing.
- `deep_fix_plans` is advisory tooling for the executor; `verify_paper_audits.sh` and `paper-writing` Phase 6 do not block on its content or shape.

### Optional: `details.restatement_drift` (only when `--restatement-check` is set)

```json
"details": {
  ...
  "restatement_drift": [
    {
      "label": "thm:main",
      "canonical_location": "sections/2.setup.tex:117",
      "restatement_location": "sections/appendix.tex:1614",
      "drift_type": "conditional_loss" | "scope_change" | "quantifier_loss" |
                    "regime_envelope_change" | "constant_change" | "variable_rename",
      "canonical_excerpt": "<short LaTeX>",
      "restatement_excerpt": "<short LaTeX>",
      "severity": "MAJOR" | "MINOR" | "CRITICAL",
      "note": "..."
    }
  ],
  "restatement_check_status": "ok" | "unavailable"
}
```

Field semantics:
- Both `restatement_drift` and `restatement_check_status` are **omitted entirely** when the flag is not set. The default schema does not include either key.
- When the flag is set and the cross-location scan completes, `restatement_check_status` is `"ok"` and `restatement_drift` lists detected pairs (possibly empty if none found).
- When the scan fails (per "Failure mode" in Phase 3.6), `restatement_check_status` is `"unavailable"` and `restatement_drift` is `[]`.
- Downstream consumers MUST treat absence or `"unavailable"` identically as the default state and MUST NOT raise on missing.
- `restatement_drift` does **not** alter `details.issues` and does **not** change the top-level `verdict` decision rule. The reviewer may at its discretion mirror a CRITICAL-severity drift into `details.issues` as a regular issue, but that is a per-issue judgment, not an automatic schema-driven rule.

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

