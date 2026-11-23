<!-- EI-WORKFLOW-REFERENCE -->

# Phase 5.6: Kill-Argument Adversarial Review (theory / scope-heavy papers)

Read this file when the workflow reaches Phase 5.6: Kill-Argument Adversarial Review (theory / scope-heavy papers) through Phase 6: Final Report. In commands and examples, interpret relative skill paths from the entrypoint directory.

### Phase 5.6: Kill-Argument Adversarial Review (theory / scope-heavy papers)

After Phase 5.5 (claim audit) passes, run `/kill-argument` whenever the paper is theory-heavy or makes explicit scope/generality claims in the title or abstract. This is a final adversarial check that complements the claim/citation/proof audits: those verify *local correctness* (numbers match, cites resolve, theorems prove); kill-argument tests *headline-level* survival — whether the paper as a whole answers the worst rejection paragraph a senior area chair would write.

```bash
THEORY_ENV_COUNT=$(rg -c '\\begin\{(theorem|lemma|proposition|corollary)\}' paper/main.tex paper/sections 2>/dev/null | awk -F: '{s+=$2} END {print s+0}')
SCOPE_HINT=$(rg -i 'general(ization)?|broad|universal|across|any [A-Za-z]+ model|holds for' paper/sections/0*abstract* 2>/dev/null | head -1)

if [ "$THEORY_ENV_COUNT" -ge 5 ] || [ -n "$SCOPE_HINT" ]; then
    /kill-argument "paper/"
    KILL_VERDICT=$(jq -r '.verdict' paper/KILL_ARGUMENT.json)
    KILL_REASON=$(jq -r '.reason_code' paper/KILL_ARGUMENT.json)
fi
```

**Gating** (depends on the resolved `assurance` level from Phase 0):

| Assurance level | THEORY/SCOPE detected | Behavior |
|---|---|---|
| `submission` | yes | **MANDATORY**. `FAIL` blocks the final report; `WARN` requires explicit user acknowledgment; `BLOCKED`/`ERROR` blocks the final report (cannot ship without an adversarial pass). |
| `submission` | no | Skip — `KILL_ARGUMENT.json` is written with `verdict: NOT_APPLICABLE, reason_code: not_theory_or_scope_paper` so the submission verifier sees a record. |
| `internal` / `draft` | yes | **Advisory**. Run if the user passed `— kill-argument: true`; otherwise skip. `WARN`/`FAIL` is logged but does not block. |
| `internal` / `draft` | no | Skip. |

`/kill-argument` itself never edits the paper; it writes `KILL_ARGUMENT.{md,json}`. If `still_unresolved critical` points are surfaced, queue them for the next `/auto-paper-improvement-loop` round (Step 5.5 of that skill auto-merges the findings into its fix list).

**Why this is the right place:** Phase 5 (loop) optimizes for score, Phase 5.5 (claim audit) verifies numbers, Phase 5.8 (citation audit) verifies cites — none of these catches the case where every local component is correct but the paper still oversells what it actually proves. Kill-argument is the dedicated headline-scope check.

### Phase 5.8: Citation Audit (submission gate)

After the final paper-claim-audit passes, run `/citation-audit` to verify every `\cite{...}` along three axes: existence, metadata correctness, and context appropriateness. This is the fourth and final layer of the evidence-and-claim assurance stack (`experiment-audit` → `result-to-claim` → `paper-claim-audit` → `citation-audit`).

```
if paper/references.bib (or paper.bib) exists and contains entries cited from sec/*.tex:
    Run /citation-audit "paper/"
    Fresh cross-family reviewer (gpt-6-astra via Codex MCP) with web/DBLP/arXiv lookup
    verifies each entry:
      (i)   EXISTENCE — paper resolves at claimed arXiv ID / DOI / venue
      (ii)  METADATA — author names, year, venue, title match canonical sources
      (iii) CONTEXT — cited paper actually establishes the claim it supports

    Output:
      - CITATION_AUDIT.md (human-readable per-entry verdict report)
      - CITATION_AUDIT.json (machine-readable verdict ledger)
      - Per-entry verdicts: KEEP / FIX / REPLACE / REMOVE

    If any REPLACE or REMOVE verdicts:
        Surface to user for human approval — never auto-modify content claims
    If only FIX verdicts (metadata corrections):
        Apply with user confirmation, then recompile
    If all KEEP:
        Pass — bibliography clean for submission
else:
    skip — no bib file or no citations
```

**Why this is the most diagnostic of the four audit layers:** wildly fake citations are easy to spot. The dangerous failure mode is a real paper used to support a claim it does not actually establish (wrong-context citations) — these slip past metadata-only checks and damage submission credibility. Run cost is wall-clock heavy (web lookup per entry); run once per submission, not per save.

**Empirical motivation:** in a real submission run, several real papers were cited in contexts they did not actually support, and at least one bib entry shipped with `author = "Anonymous"` because the metadata had not been resolved. None were caught by the improvement loop or numeric claim audit; only fresh web-lookup review surfaced them.

### Phase 5.9: Integrity Forensics (submission self-audit — default ON)

Run the [`/integrity-forensics`](../../integrity-forensics/SKILL.md) launcher on
`paper/` (ABSOLUTE path): the SHA-pinned Anti-Autoresearch sweep — evidence
ledger, nine auditor dimensions, deterministic adjudication — followed by the
typed policy gate and the append-only obligations ledger. Self-auditing runs
at whatever observability the artifacts allow (with `code/` + `results/`
present that is L2 — stricter than anything an external reviewer can run).

**When it runs** (re-derive here — do NOT trust `.ei/assurance.txt` alone;
a resumed run whose Phase 0 never executed, or whose file went stale, must
not silently skip the default-ON gate):

1. Re-derive the assurance level from `$ARGUMENTS` with the **same rule as
   Phase 0 / Phase 6.0** (explicit `— assurance:` wins; else `max`/`beast` →
   `submission`; else `draft`).
2. Parse `$ARGUMENTS` for `— self_forensics: true | false`.
3. Then:
   - `submission` → **ON by default**. Opt out only with an explicit
     `— self_forensics: false` — persist the receipt as a record:
     `mkdir -p paper/.ei/forensics && echo "opted-out: — self_forensics: false in \$ARGUMENTS" > paper/.ei/forensics/opt_out.txt`
     (recorded in the Final Report as `Forensics: skipped (opted out)`).
     The receipt documents THIS run's decision; it does not authorize any
     later run to skip — Phase 6.0 re-parses `$ARGUMENTS` itself.
   - `draft` → off unless `— self_forensics: true`.

**Gate handling** (exit 1 = `BLOCK`: upstream `HARD_FLAGS`,
`REVIEW_UNAVAILABLE`, or an OPEN critical obligation):
- Refuse the Final Report — same discipline as a verifier `FAIL`. Surface the
  upstream `REPORT.md` and the obligations verbatim; never paraphrase-soften.
- Route each obligation to its repair door (the family table in
  `/integrity-forensics` Step 3): numeric → recompute from result files;
  citations → `/citation-audit`; proof → `/proof-checker`; scope/baseline/
  eval-design → `/auto-review-loop` as reviewer input, or the human.
- Close obligations ONLY via `forensics_gate.py resolve` (typed, hashed
  evidence) or a human `waive`. Since 2026-08 upstream reports every proposal an
  auditor made rather than deciding which ones do not count, so expect more
  obligations and expect some to be proposals you judge wrong — `waive` with a
  reason is the normal disposition for those, not a last resort. **Never edit the
  paper with the objective "make the sweep stop flagging"** — a
  vanished-but-unresolved finding keeps the gate closed
  (`UNRESOLVED_DISAPPEARANCE`).
- `WARN` (SOFT_FLAGS / open non-critical obligations): proceed, but the Final
  Report must list them under `Forensics` — including the dimensions the sweep
  never ran, which `evaluate` and `fresh` both print. A WARN can sit on top of an
  incomplete sweep: upstream folds incompleteness into the verdict only when it
  would otherwise read clean.
- Zero-weight AIS style impressions: FYI only — may feed
  `/auto-paper-improvement-loop` context, never gate.

### Phase 6: Final Report

**Phase 6.0 — Submission Gate**

Before writing the Final Report, resolve the active assurance level. This
uses the **same derivation rule as Phase 0** so a run where Phase 0 was
skipped or its write failed cannot silently downgrade a `beast` / `max` /
`— assurance: submission` invocation back to draft.

**Resolution at the gate** (re-derive; do not trust `.ei/assurance.txt`
alone):

1. Parse `$ARGUMENTS` for an explicit `— assurance: draft | submission` or
   an `— effort: lite | balanced | max | beast` directive.
2. Derive the expected level:
   - explicit `assurance:` wins
   - else `lite` / `balanced` → `draft`, `max` / `beast` → `submission`
   - else `draft`
3. Read `paper/.ei/assurance.txt`. If the file is missing, write it now
   with the derived level.
4. If the file's value **disagrees** with the derived level (e.g. file
   says `draft` but `$ARGUMENTS` says `beast`), **overwrite** the file
   with the derived level and surface a one-line warning in-chat:
   `⚠️ .ei/assurance.txt was draft but $ARGUMENTS says submission; overriding.`
5. Use the re-derived level as authoritative for the rest of Phase 6.

```bash
# Final authoritative value, written and read from the same source
ASSURANCE=<derived-from-$ARGUMENTS>        # draft | submission
mkdir -p paper/.ei
echo "$ASSURANCE" > paper/.ei/assurance.txt
```

If `ASSURANCE=draft`, skip directly to the Final Report template below —
**current behavior, no change** for the default `balanced` user.

If `ASSURANCE=submission`, run the pre-flight checklist below, then the
verifier. The verifier's exit code is the source of truth — do NOT
self-declare "audits complete" based on conversation memory.

