<!-- EI-WORKFLOW-REFERENCE -->

# Phase 3.6: Theorem Restatement Regression (opt-in)

Read this file when the workflow reaches Phase 3.6: Theorem Restatement Regression (opt-in) through Key Rules. In commands and examples, interpret relative skill paths from the entrypoint directory.

### Phase 3.6: Theorem Restatement Regression (opt-in)

**Default**: skipped. Existing callers see no change.

**Opt-in**: pass `--restatement-check` on invocation. The skill then runs a cross-location consistency pass after Phase 3.5 (Global Closure) and before Phase 3.9 (Unrecoverable Protocol).

This phase catches a specific class of bugs that Phase 3.5's "Statement-conclusion match" check does NOT catch: **drift between the canonical theorem statement and its restatements elsewhere in the paper** (summary tables, "Key Contributions" / "Summary" sections, abstract, discussion, captions). Common drift patterns observed in practice:

- Main theorem makes a partly-conditional claim (e.g., "regime A unconditional, regime B conditional on assumption X") but a later summary cites it as the fully unconditional version.
- Main theorem κ exponent is `O(d²K²)` but a constants table writes `O(K²)`.
- Main theorem regime condition is squared envelope, but a remark elsewhere still shows the first-order envelope.
- Restatement quietly drops a quantifier ("for $n \ge n_0$") that the proof relied on.

#### Algorithm

1. **Build canonical statement table.** Scan all `*.tex` files in the paper for `\begin{theorem}` / `\begin{lemma}` / `\begin{proposition}` / `\begin{corollary}` blocks with a `\label{...}`. For each: record `(label, full_statement_text, file:line_range)`.

2. **Collect restatement candidates.** For each canonical label `thm:foo`:
   - Every `\Cref{thm:foo}` / `\ref{thm:foo}` / `\cref{thm:foo}` invocation, with the surrounding 2 sentences as candidate restatement context.
   - Rows in tables (`\begin{tabular}` … `\end{tabular}`) that mention the label, the theorem's informal name, or its constants.
   - Bullets in "Key Contributions" / "Summary" / "Main Results" lists.
   - Sentences in the abstract and introduction that paraphrase the theorem.

3. **Normalized diff.** For each (canonical_statement, restatement_context) pair:
   - Strip `\,` `\;` `\!` `~`, normalize whitespace, normalize math-mode delimiters (`$..$`, `\(..\)`, display vs inline).
   - Detect drift signatures (one or more):
     - **conditional_loss** — canonical says "under \Cref{ass:X}" or "for w=1"; restatement omits the conditional.
     - **scope_change** — big-O exponent or rate differs (`O(K^2)` vs `O(d^2K^2)`; `√n` vs `n`).
     - **quantifier_loss** — quantifier present canonically (e.g. "for $n \ge n_0$", "for sufficiently small $\gamma$") absent in restatement.
     - **regime_envelope_change** — first-order leakage `Cγ/(1-Δγ)` vs squared envelope `(Cγ/(1-Δγ))²` (or analogous).
     - **constant_change** — different numeric constant or different parameter dependence stated.
     - **variable_rename** — same role in argument played by differently-named symbol with no explicit alias.

4. **Emit findings.** Each detected drift becomes an entry in `details.restatement_drift` (see "Submission Artifact Emission" below). Severity defaults to **MAJOR** (UNDERSTATED/OVERSTATED + GLOBAL); reviewer may downgrade to MINOR if drift is purely cosmetic (e.g. `\,` placement) and upgrade to CRITICAL only if the restatement is used downstream as if it were the canonical (e.g. another proof cites the restated version).

#### What this phase does NOT do
- It does **not** fix drift automatically. The output is advisory; the executor or a follow-up `--deep-fix` run handles the rewrite.
- It does **not** alter `details.issues`; restatement drift is reported as a sibling field, so existing consumers reading `issues[]` see no schema change.
- It does **not** alter the top-level `verdict` decision rule. A paper with non-empty `restatement_drift` may still emit `PASS` if all proof obligations are otherwise discharged; the drift is independent of proof correctness. (The reviewer may at its discretion mirror a **CRITICAL**-severity drift into the `issues` list as a regular issue — typically when the restated version is used downstream as if it were canonical — but that is a per-issue judgment, never an automatic rule. MAJOR or MINOR drift never mirrors into `issues`.)

#### Failure mode
If `--restatement-check` is set but the cross-location scan cannot complete, emit `details.restatement_drift: []` plus `details.restatement_check_status: "unavailable"` with a one-line note explaining why. Verifier gates and downstream skills MUST treat `"unavailable"` identically to the field being absent: not blocking. Phases 1 / 1.5 / 2 / 3 / 3.5 / 3.9 / 4 / 5 still run normally. Cases that trigger this fallback include:
- Unreadable `.tex` (parser / encoding error on a file that contains a theorem block).
- Ambiguous label resolution (e.g., the same `\label{thm:foo}` appears more than once with no clear canonical pick).
- **No labeled canonical theorem-like block found** (the algorithm only inspects `\begin{theorem|lemma|proposition|corollary}` blocks with an explicit `\label{...}`; if there is no such block, there is nothing to compare restatements against).

### Phase 3.9: Unrecoverable Proof Protocol

If acceptance gate is not met after MAX_REVIEW_ROUNDS, output a **Proof Unrecoverable Report**:
1. Minimal set of blocking FATAL/CRITICAL issues that could not be resolved
2. Salvage options ranked: (a) weaken claim, (b) strengthen assumptions, (c) add missing lemmas, (d) restructure argument
3. Which parts of the proof are likely still reusable
4. Recommended next steps for the author

Do NOT silently declare success. The report must be honest.

### Phase 4: Audit Report Generation

Generate `proof_audit_report.tex` with:

1. **Overview table**: All issues with two-axis severity, category, fix strategy, status
2. **Before/After logic chain**: Red (BEFORE) → Green (AFTER) comparison
3. **For each fix**: original proof → why wrong → counterexample (if any) → complete derivation → remaining subtleties
4. **Proof-obligation diff**: What was unverified before, what is verified now
5. **Summary**: Now proven / still assumed / open problems
6. **Colored boxes**: BEFORE (red), AFTER (green), WHY WRONG (orange), KEY INSIGHT (blue), WARNING (yellow)

Compile: `pdflatex proof_audit_report.tex && pdflatex proof_audit_report.tex`

### Phase 5: State Persistence

Write `PROOF_CHECK_STATE.json`:
```json
{
  "status": "completed",
  "rounds": 2,
  "threadId": "...",
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

If — and only if — a `research-wiki/` exists, persist each top-level
theorem/headline as a **claim node** so the wiki's PROVE/JUDGE ledger records what
was proven and with what honesty. This is the **birth point** for wiki claim nodes
(`claims/<slug>.md`). It is a **detect-only record, never a verdict**: it never
changes the audit's `verdict`/`reason_code`, never blocks, and is skipped entirely
when `verdict == NOT_APPLICABLE` (no theorems) or no wiki is found.

> The claim's `status` is the **PROOF axis only** (`verified` / `sound-modulo-imports`
> / `refuted` / `unproven` / `drafted` / `retracted`). Empirical experiment support is
> a **separate axis** carried by `supports` / `invalidates` *edges* from
> `/result-to-claim` — those words are NEVER written into this `status` field (the
> `research_wiki.py` validator rejects them).

Resolve the helper via the **canonical resolver** (integration-contract §2). Check
`NOT_APPLICABLE` first (in cwd, where the audit ran), then run from the project root
(the wiki sits at root; a paper audit may run from a `paper/` subdir). Every guard
warn-and-skips — the audit is already complete and is never affected:

```bash
grep -q '"verdict"[[:space:]]*:[[:space:]]*"NOT_APPLICABLE"' PROOF_AUDIT.json 2>/dev/null \
  && { echo "verdict NOT_APPLICABLE (no theorems); skipping claim ledger" >&2; exit 0; }
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 0
[ -d research-wiki ] || { echo "no research-wiki/ at project root; skipping claim ledger (audit complete)" >&2; exit 0; }
if [ -z "${ARIS_REPO:-}" ] && [ -f .ei/installed-skills.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills.txt 2>/dev/null) || true
fi
if [ -z "${ARIS_REPO:-}" ] && [ -f "$HOME/.ei/repo" ]; then
    ARIS_REPO=$(cat "$HOME/.ei/repo" 2>/dev/null) || true
fi
WIKI_SCRIPT=".ei/tools/research_wiki.py"
[ -f "$WIKI_SCRIPT" ] || WIKI_SCRIPT="tools/research_wiki.py"
[ -f "$WIKI_SCRIPT" ] || { [ -n "${ARIS_REPO:-}" ] && WIKI_SCRIPT="$ARIS_REPO/tools/research_wiki.py"; }
[ -f "$WIKI_SCRIPT" ] || { echo "WARN: research_wiki.py not resolved; skipping claim ledger (audit unaffected)" >&2; exit 0; }
```

For each top-level theorem/headline in `PROOF_SKELETON.md` (the main theorem + the
key lemmas the headline depends on — NOT every micro-claim), map the audit outcome
to an **honest** claim status:

| Audit outcome (`PROOF_AUDIT.json` verdict + Phase 1.5 counterexamples) | `--status` |
|---|---|
| `verdict=PASS` / `all_proofs_complete`, no flagged imports | `verified` |
| proof closes but rests on a flagged `[unverified-axiom]` / imported result | `sound-modulo-imports` |
| counterexample found (Phase 1.5) **or** reviewer judged the statement false | `refuted` |
| open gap (unresolved FATAL/CRITICAL / UNJUSTIFIED, no counterexample) | `unproven` |

Never invent a status: a plain proof gap is `unproven` — never `refuted` (which
asserts falsity) and never `verified`/`drafted`. Then record (idempotent):

```bash
python3 "$WIKI_SCRIPT" add_claim research-wiki/ \
  --slug "<stable-theorem-id, e.g. thm-main-ub>" --name "<theorem headline>" \
  --status "<mapped status>" --provenance "<trace_path from PROOF_AUDIT.json>" \
  --statement "<canonical theorem statement>" \
  --scope "<what it does NOT say; any flagged imports>" \
  --evidence "<PROOF_AUDIT.json verdict + counterexample / obligation pointers>" \
  --update-on-exist \
  || echo "WARN: add_claim failed for <slug> (audit unaffected; fix wiki/status and re-run)" >&2
```

`--update-on-exist` lets a re-audit refresh a claim's status (an `unproven` claim
becomes `verified` once the gap closes). `--provenance` is the honesty receipt (the
`trace_path`); never omit it.

## Deep-Fix Mode (opt-in)

**Default**: disabled. The Phase 1 reviewer emits issues with `minimal_fix` (a 1-2 sentence pointer); existing callers see no change.

**Opt-in**: pass `--deep-fix` on invocation. The Phase 1 reviewer prompt is **augmented** (not replaced) with the "DEEP-FIX OUTPUT" and "ALGEBRA / TYPE SANITY PASS" blocks above, so the reviewer also returns a `deep_fix_plan` per issue: corrected statement, changed equations, downstream label list, minimal LaTeX patch plan, and closure tests. Issues invoking Schur / Young / Cauchy-Schwarz / Hölder / quadratic forms / operator norms / power counting additionally carry an `algebra_sanity` block (dimension table + power count + zero-coupling check + constant-dependence diff).

### Why opt-in
The default `minimal_fix` prose is intentionally short — it suits the common case where the executor wants high-level pointers and will derive the patch separately. Forcing `deep_fix_plan` on every run would (a) inflate every reviewer call by 2-5×, (b) trigger re-review thrash for issues the executor has already decided to weaken or defer, and (c) change the shape of `details.issues` for every existing caller. The flag preserves zero behavior change for default invocations while letting the executor request repair-grade output when the fix is going to be applied immediately.

### Effect when enabled
- The Phase 1 reviewer prompt is augmented with the deep-fix and algebra-sanity blocks; nothing in the original mandatory checklist or output format is removed.
- `PROOF_AUDIT.json` `details` gains a sibling field `deep_fix_plans` (parallel to `details.issues`); see "Submission Artifact Emission" below.
- The top-level `verdict`, `reason_code`, and `summary` are **unchanged in shape and decision rule**: deep-fix output is advisory tooling for the executor, not a verdict-altering signal.
- Verifier gates and downstream skills (`paper-writing` Phase 6, `verify_paper_audits.sh`) MUST treat absence of `deep_fix_plans` as the only valid default state and MUST NOT block on its presence or content.

### When opt-in is appropriate
- The executor intends to apply the fix in the same session and wants to skip a follow-up "give me a concrete patch" thread.
- A previous default-mode run identified a CRITICAL or MAJOR issue whose `minimal_fix` was too vague to act on (e.g., "redo the Schur step" without specifying the corrected operator-norm bound).
- Algebra-heavy proofs with Schur / quadratic-form / operator-norm steps where the reviewer's first pass has consistently produced under-specified fixes.

### Failure modes

A deep-fix-only failure must never contaminate the default proof-check output. All of the following paths emit `details.deep_fix_status: "unavailable"` + `details.deep_fix_plans: []` (with a one-line note in `details.deep_fix_note`) and leave the standard issue list, top-level verdict, reason_code, and summary unchanged:

- The reviewer refuses to produce a repair-grade plan because the fix would require choices the reviewer is unwilling to make.
- The Phase 1 reviewer call returns truncated or malformed deep-fix output (parse failure on the augmented section).
- The augmented Phase 1 call times out before producing the deep-fix block, but otherwise returned a valid normal proof review.

Verifier gates MUST treat `unavailable` identically to the field being absent: not blocking. Do **not** add a `UNCLEAR_DEEP_FIX` (or any deep-fix-only) entry into `details.issues`, since `details.issues` is the default schema's issue list and adding deep-fix-specific failures to it would change default behavior for callers without the flag.

If the augmented Phase 1 call fails so badly that the normal proof review cannot be recovered (e.g., the reviewer thread itself errored), retry once with the unaugmented prompt **only when the error proves the call never executed** (schema/validation or explicit capability error per the fallback chain in `reviewer-routing.md`); on timeout, rate-limit, transport, or server errors do NOT blind-retry (the review may have run — double-running double-bills), fall through directly to the existing reviewer-failure path that maps to the top-level `ERROR` verdict.

## Key Rules

