<!-- EI-WORKFLOW-REFERENCE -->

# Submission pre-flight checklist

Read this file when the workflow reaches Submission pre-flight checklist through Running the verifier. In commands and examples, interpret relative skill paths from the entrypoint directory.

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
   [ ] 4. Resolve $AUDIT_VERIFIER per integration-contract.md §2 (Policy A),
          then: bash "$AUDIT_VERIFIER" paper/ --assurance submission
   [ ] 5. Integrity forensics (Phase 5.9, default ON at submission). FIRST
          re-parse the CURRENT $ARGUMENTS — an opt_out.txt receipt left by a
          PREVIOUS run never carries over; it is a record for the report line,
          not an authorization.
          - current $ARGUMENTS has `— self_forensics: false` → skipping is
            legal; write/refresh paper/.ei/forensics/opt_out.txt.
          - otherwise the whole check is ONE command:
            `python3 "$GATE_HELPER" fresh --paper-dir paper/ --anti-ar-commit
            "$ANTI_AR_COMMIT"` (the pin constant from /integrity-forensics;
            an old-pin gate must be re-audited) — exit 0 ⟺ a
            gate exists ∧ no paper file changed after it ∧ it matches the
            current obligations ledger ∧ its decision is pass-capable (an
            ALLOWLIST: WARN / NO_NEW_BLOCKER — an unknown or missing token
            never passes). Exit 1 → the sweep never saw this text (or the
            gate is BLOCK): run Phase 5.9 NOW, before the Final Report —
            BLOCK is blocked, same as a verifier FAIL.
   [ ] 6. Block Final Report iff verifier exit code != 0 OR row 0 found a
          violated undisputed assertion OR row 5 is red. (THREE separate
          gates: row 0 is graded by instruction against the contract; the
          verifier checks audit JSONs only — verify_paper_audits.sh does NOT
          read the contract; row 5 reads the forensics gate artifact.)
```

> The resolver in "Running the verifier" below tries
> `.ei/tools/verify_paper_audits.sh` (created by `install_aris.sh`),
> then `tools/verify_paper_audits.sh` (in-repo run), then
> `$ARIS_REPO/tools/verify_paper_audits.sh` (env-var-set or manifest-derived
> path), then the same `$ARIS_REPO/tools/verify_paper_audits.sh` resolved via
> the global pointer file `~/.ei/repo` (#366). The chain always tries
> layers 1 → 2 → 3 → 4 in order; setting `export ARIS_REPO=~/…` only ensures
> layer 3 has a valid target if layers 1 and 2 are absent, and layer 4 only
> fires when neither the env var nor the project manifest set `ARIS_REPO`.

#### Invoking the four audits

Each sub-audit runs in a **fresh Codex thread** (never `codex-reply`,
never pass prior audit output as context — this preserves reviewer
independence per `shared-references/reviewer-independence.md`).

Each sub-audit **always** emits its JSON artifact, even when the content
detector is negative. A detector-negative run emits verdict
`NOT_APPLICABLE`; a silent skip is forbidden. See the "Submission artifact
emission" section of each audit's SKILL.md.

Order:

1. `/proof-checker "paper/"` → writes `paper/PROOF_AUDIT.json` (emits
   `NOT_APPLICABLE` if the paper contains no theorems / lemmas / proofs)
2. `/paper-claim-audit "paper/"` → writes `paper/PAPER_CLAIM_AUDIT.json`
   (emits `NOT_APPLICABLE` if the paper has no numeric claims; emits
   `BLOCKED` if numeric claims exist but raw result files are missing)
3. `/citation-audit "paper/"` → writes `paper/CITATION_AUDIT.json`
   (emits `NOT_APPLICABLE` if no `.bib` file or no `\cite{...}` usage)
4. `paper/KILL_ARGUMENT.json` was already written in Phase 5.6 (including the
   `NOT_APPLICABLE` record for non-theory papers) — the verifier requires all four.

#### Running the verifier

Resolve `$AUDIT_VERIFIER` via the canonical strict-safe chain (see
[`shared-references/integration-contract.md`](../../shared-references/integration-contract.md)
§2, Policy A — gate). Under `assurance: submission` the verifier is
load-bearing: if the helper is unresolved the SKILL aborts the Final
Report rather than producing an unverified `submission-ready` claim.

```bash
# Resolve the audit verifier (Policy A — gate).
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 1
if [ -z "${ARIS_REPO:-}" ] && [ -f .ei/installed-skills.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills.txt 2>/dev/null) || true
fi
if [ -z "${ARIS_REPO:-}" ] && [ -f "$HOME/.ei/repo" ]; then
    ARIS_REPO=$(cat "$HOME/.ei/repo" 2>/dev/null) || true
fi
AUDIT_VERIFIER=".ei/tools/verify_paper_audits.sh"
[ -f "$AUDIT_VERIFIER" ] || AUDIT_VERIFIER="tools/verify_paper_audits.sh"
[ -f "$AUDIT_VERIFIER" ] || { [ -n "${ARIS_REPO:-}" ] && AUDIT_VERIFIER="$ARIS_REPO/tools/verify_paper_audits.sh"; }
[ -f "$AUDIT_VERIFIER" ] || {
  echo "ERROR: verify_paper_audits.sh not resolved at .ei/tools/, tools/, \$ARIS_REPO/tools/, or via ~/.ei/repo." >&2
  echo "       assurance=submission requires the verifier; aborting Final Report." >&2
  echo "       Fix: rerun bash tools/install_aris.sh or smart_update.sh (refreshes ~/.ei/repo), export ARIS_REPO, or copy the helper to tools/." >&2
  exit 1
}

bash "$AUDIT_VERIFIER" paper/ --assurance submission
```

- **Exit 0** — All mandatory audits present, JSON schema-valid, hashes fresh,
  no blocking verdicts. **Before writing the Final Report, read
  `overall_assurance` from `paper/.ei/audit-verifier-report.json`** — exit 0
  covers BOTH `accepted` (cross-family/independent review) and `provisional`
  (same-family or legacy review that may proceed but must not claim
  independent acceptance). The Final Report's Submission-ready line comes from
  that field, never from the exit code alone.
- **Exit 1** — Surface `paper/.ei/audit-verifier-report.json` to the user
  verbatim, **refuse to generate the Final Report**, and list the specific
  remediation for each failing row:
  - `MISSING` → rerun that audit
  - `STALE` → paper files edited after the audit ran; rerun the affected audit
  - `BLOCKING_VERDICT` (FAIL / BLOCKED / ERROR) → fix the underlying issue,
    then rerun the audit
  - `SCHEMA_INVALID` → audit artifact malformed; rerun the audit

The verifier is cheap to rerun (< 1 s). After fixing any issue, rerun it
before claiming green.

