<!-- EI-WORKFLOW-REFERENCE -->

# Phase 5: Auto Improvement Loop

Read this file when the workflow reaches Phase 5: Auto Improvement Loop through Submission pre-flight checklist. In commands and examples, interpret relative skill paths from the entrypoint directory.

### Phase 5: Auto Improvement Loop

Invoke `/auto-paper-improvement-loop` to polish the paper:

```
/auto-paper-improvement-loop "paper/"
```

**What this does (2 rounds):**

**Round 1:** GPT-6-Astra xhigh reviews the full paper → identifies CRITICAL/MAJOR/MINOR issues → Claude Code implements fixes → recompile → save `main_round1.pdf`

**Round 2:** GPT-6-Astra xhigh re-reviews the recompiled draft cold (fresh review — no fix summaries, no conversation carry-over) → identifies remaining issues → Claude Code implements fixes → recompile → save `main_round2.pdf`

**Typical improvements (calibration cuts both ways):**
- Fix assumption-model mismatches
- Narrow genuine overclaims to the supported scope — and state supported claims
  directly, removing redundant hedges
- Consolidate scattered generic caveats into Limitations
- Add missing interpretations and notation
- Make Limitations more specific (only when a material limit is missing — never pad)
- Add theory-aligned experiments if needed

**Output:** Three PDFs for comparison + `PAPER_IMPROVEMENT_LOG.md`.

**Format check** (included in improvement loop Step 8): After final recompilation, auto-detect and fix overfull hboxes (content exceeding margins), verify page count vs venue limit, and ensure compact formatting. Location-aware thresholds: any main-body overfull blocks completion regardless of size; appendix overfulls block only if >10pt; bibliography overfulls block only if >20pt.

### Phase 5.5: Final Paper Claim Audit (MANDATORY submission gate)

After `/auto-paper-improvement-loop` finishes, **rerun** `/paper-claim-audit` before the final report whenever the paper contains numeric claims and machine-readable raw result files exist.

Use the same detectors as Phase 4.7:
- numeric-claim regex over `paper/main.tex` and `paper/sections/*.tex`
- raw-evidence file search in `results/`, `outputs/`, `experiments/`, and `figures/` for `.json`, `.jsonl`, `.csv`, `.tsv`, `.yaml`, or `.yml`

This phase is **mandatory** if both detectors are positive. It blocks the final report.
If numeric claims exist but no raw result files are found, stop and warn the user before declaring the paper complete.
If no numeric claims exist, skip.

```bash
NUMERIC_CLAIMS=$(rg -n -e '[0-9]+(\.[0-9]+)?\s*(%|\\%|±|\\pm|x|×)' \
  -e '(accuracy|BLEU|F1|AUC|mAP|top-1|top-5|error|loss|perplexity|speedup|improvement)' \
  paper/main.tex paper/sections 2>/dev/null || true)

RAW_RESULT_FILES=$(find results outputs experiments figures -type f \
  \( -name '*.json' -o -name '*.jsonl' -o -name '*.csv' -o -name '*.tsv' -o -name '*.yaml' -o -name '*.yml' \) 2>/dev/null | head -200)

if [ -n "$NUMERIC_CLAIMS" ] && [ -n "$RAW_RESULT_FILES" ]; then
    Run /paper-claim-audit "paper/"
    If FAIL:
        Fix mismatched numbers before the final report
elif [ -n "$NUMERIC_CLAIMS" ]; then
    Stop and warn: the paper contains numeric claims but no raw evidence files were found
fi
```

**Empirical motivation:** in a real submission run, the final paper claimed a narrower experiment grid than the raw JSON actually contained, and a tolerance value was rounded down past the actual relative error. Both were caught only after manual `paper-claim-audit` invocation in the final round; the improvement loop did not detect them.

### Phase 5.8: Citation Audit (submission gate)

After the final paper-claim-audit passes, run `/citation-audit` to verify every `\cite{...}` along three axes: existence, metadata correctness, and context appropriateness. This is the fourth and final layer of the evidence-and-claim assurance stack (`experiment-audit` → `result-to-claim` → `paper-claim-audit` → `citation-audit`).

```
if paper/references.bib (or paper.bib) exists and contains entries cited from sec/*.tex:
    Run /citation-audit "paper/"
    Fresh Codex reviewer (`spawn_agent`, same-family provisional) with web/DBLP/arXiv lookup
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

### Phase 5.9: Integrity Forensics (optional here — see Codex-native note)

The mainline pipeline defaults to a pre-submission Anti-Autoresearch sweep
(`/integrity-forensics` launcher: SHA-pinned clone, evidence ledger, nine
auditor dimensions, deterministic adjudication, typed BLOCK/WARN/NO_NEW_BLOCKER
gate + append-only obligations). **In a Codex-native session this is OFF by
default**: upstream ships no Codex-native pack, so only its deterministic-only
mode is runnable here (numeric core + adjudicator with an all-unavailable
coverage map — it can flag, it can never say CLEAN; translating upstream's
reviewer calls into `spawn_agent` would rewrite an upstream contract and is
forbidden). Run it with `— self_forensics: true` for the deterministic slice,
or run the full sweep from a Claude Code session. If it runs: gate `BLOCK`
refuses the Final Report; the gate records `same-family` proposal provenance
for a Codex executor — informational, since this gate only raises flags and
grants nothing. An opted-in run (`— self_forensics: true` in `$ARGUMENTS` —
re-check `$ARGUMENTS` at Phase 6.0, not conversation memory) that reaches the
Final Report without `paper/.ei/forensics/gate.json` is **incomplete, not
skippable**: run the slice before reporting.

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

#### Submission pre-flight checklist

Print this checklist verbatim at the start of Phase 6.0 and confirm each row
before proceeding. This resists the common failure mode of the model
skipping audits while claiming to have run them.

```
📋 Submission audits required before Final Report:
   [ ] 0. PAPER_ACCEPTANCE_CONTRACT.md (Phase 1.5): re-read every assertion
          against the final PDF + results files; each → satisfied / violated /
          disputed-at-negotiation. ANY violated undisputed assertion blocks the
          Final Report until fixed or the human explicitly waives it (waivers
          recorded in the contract file). Contract absent (pre-1.5 run) → mark
          "no contract" and continue.
   [ ] 1. /proof-checker        → paper/PROOF_AUDIT.json
   [ ] 2. /paper-claim-audit    → paper/PAPER_CLAIM_AUDIT.json
   [ ] 3. /citation-audit       → paper/CITATION_AUDIT.json
   [ ] 4. Resolve $AUDIT_VERIFIER per integration-contract §2 (Policy A),
          then: bash "$AUDIT_VERIFIER" paper/ --assurance submission
   [ ] 5. Integrity forensics (Phase 5.9 — OPT-IN here): re-parse the CURRENT
          $ARGUMENTS. If it contains `— self_forensics: true`, require
          `python3 "$GATE_HELPER" fresh --paper-dir paper/ --anti-ar-commit
          "$ANTI_AR_COMMIT"` exit 0 (produced at the current pin; gate
          exists ∧ paper unchanged since ∧ ledger-bound ∧ decision
          pass-capable). Exit 1 → the deterministic slice never saw this
          text: run Phase 5.9 NOW. Not opted in → mark "n/a (opt-in)".
   [ ] 6. Block Final Report iff verifier exit code != 0 OR row 0 found a
          violated undisputed assertion OR row 5 is red. (THREE separate
          gates: row 0 is graded by instruction against the contract; the
          verifier checks audit JSONs only — verify_paper_audits.sh does NOT
          read the contract; row 5 reads the forensics gate artifact.)
```

> `<ARIS_REPO>` placeholder — replace with the absolute path to your ARIS
> clone (e.g. `~/Desktop/Auto-claude-code-research-in-sleep`). In a Codex
> project install, derive it from `.ei/installed-skills-codex.txt`:
> `ARIS_REPO="$(awk -F '\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills-codex.txt)"`.
> For an unmanaged flat symlink install, use the skill directory symlink:
> `ARIS_REPO="$(cd "$(readlink .agents/skills/paper-writing)/../../.." && pwd)"`.
> The path is stable across runs; store it in a shell variable if you prefer.

