<!-- EI-WORKFLOW-REFERENCE -->

# Invoking the four audits

Read this file when the workflow reaches Invoking the four audits through Typical Timeline. In commands and examples, interpret relative skill paths from the entrypoint directory.

#### Invoking the four audits

Each sub-audit runs in a **fresh Codex thread** (never a continuation reply,
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

#### Running the verifier

Resolve `$AUDIT_VERIFIER` via the canonical strict-safe chain (see
[`shared-references/integration-contract.md`](../../shared-references/integration-contract.md) §2,
Policy A — gate). Under `assurance: submission` the verifier is
load-bearing: if the helper is unresolved the SKILL aborts the Final
Report rather than producing an unverified `submission-ready` claim.

```bash
# Resolve the audit verifier (Policy A — gate; Codex-side chain).
if [ -z "${ARIS_REPO:-}" ] && [ -f .ei/installed-skills-codex.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills-codex.txt 2>/dev/null) || true
fi
AUDIT_VERIFIER=""
[ -n "${ARIS_REPO:-}" ] && [ -f "$ARIS_REPO/tools/verify_paper_audits.sh" ] && AUDIT_VERIFIER="$ARIS_REPO/tools/verify_paper_audits.sh"
[ -z "$AUDIT_VERIFIER" ] && {
  echo "ERROR: verify_paper_audits.sh not resolved at \$ARIS_REPO/tools/." >&2
  echo "       assurance=submission requires the verifier; aborting Final Report." >&2
  exit 1
}

bash "$AUDIT_VERIFIER" paper/ --assurance submission
OVERALL_ASSURANCE=$(python3 -c 'import json; print(json.load(open("paper/.ei/audit-verifier-report.json"))["overall_assurance"])')
```

- **Exit 0** — All mandatory audits present, JSON schema-valid, hashes fresh,
  no blocking verdicts. Proceed to the Final Report below. If
  `OVERALL_ASSURANCE=provisional`, the report MUST say
  `Submission-ready: provisional`; only `accepted` may say `yes`.
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

#### Optional hardening (not default)

Teams that want hook-level enforcement — i.e., the harness physically
prevents a Stop event while the verifier is red — can register an equivalent
Codex stop hook if their local Codex runtime supports hooks:

```json
{
  "hooks": {
    "Stop": [
      {"command": "bash <ARIS_REPO>/tools/verify_paper_audits.sh paper/ --assurance submission"}
    ]
  }
}
```

This is documented here, not required. Phase 6.0's verifier-as-truth
pattern is the default repo behavior.

---

**Phase 6.1 — Final Report** (runs only after the submission gate is green,
or directly if `assurance=draft`)

```markdown
# Paper Writing Pipeline Report

**Input**: [NARRATIVE_REPORT.md or topic]
**Venue**: [ICLR/NeurIPS/ICML/CVPR/ACL/AAAI/ACM/IEEE_JOURNAL/IEEE_CONF]
**Assurance**: [draft | submission]
**Submission-ready**: [yes | provisional | no]   <!-- yes iff overall_assurance=accepted; provisional iff same-family review passed -->
**Forensics**: [NO_NEW_BLOCKER | WARN: <n> open obligations | BLOCK | n/a (opt-in, not requested)]   <!-- deterministic slice only; from .ei/forensics/gate.json — a WARN's open obligations MUST be listed in this report, never silently passed -->
**Date**: [today]

## Pipeline Summary

| Phase | Status | Output |
|-------|--------|--------|
| 0. Assurance Setup | ✅ | paper/.ei/assurance.txt = [draft\|submission] |
| 1. Paper Plan | ✅ | PAPER_PLAN.md |
| 1.5 Acceptance Contract | [accepted\|contested\|no contract] ([N] rounds) | PAPER_ACCEPTANCE_CONTRACT.md |
| 2. Figures | ✅ | figures/ ([N] auto + [M] manual) |
| 3. LaTeX Writing | ✅ | paper/sections/*.tex ([N] sections, [M] citations) |
| 4. Compilation | ✅ | paper/main.pdf ([X] pages) |
| 5. Improvement | ✅ | [score0]/10 → [score2]/10 |
| 4.5 Proof Audit | [PASS\|WARN\|FAIL\|NOT_APPLICABLE\|BLOCKED\|ERROR] | PROOF_AUDIT.{md,json} |
| 5.5 Paper Claim Audit | [PASS\|WARN\|FAIL\|NOT_APPLICABLE\|BLOCKED\|ERROR] | PAPER_CLAIM_AUDIT.{md,json} |
| 5.8 Citation Audit | [PASS\|WARN\|FAIL\|NOT_APPLICABLE\|BLOCKED\|ERROR] | CITATION_AUDIT.{md,json} |
| 6.0 Assurance Verifier | [accepted\|provisional\|blocked]; exit [0\|1] overall (N/A if draft) | .ei/audit-verifier-report.json |

## Improvement Scores
| Round | Score | Key Changes |
|-------|-------|-------------|
| Round 0 | X/10 | Baseline |
| Round 1 | Y/10 | [summary] |
| Round 2 | Z/10 | [summary] |

## Deliverables
- paper/main.pdf — Final polished paper
- paper/main_round0_original.pdf — Before improvement
- paper/main_round1.pdf — After round 1
- paper/main_round2.pdf — After round 2
- paper/PAPER_IMPROVEMENT_LOG.md — Full review log
- paper/PROOF_AUDIT.{md,json} — Proof-obligation verification (always emitted at `assurance=submission`; `NOT_APPLICABLE` when no theorems)
- paper/PAPER_CLAIM_AUDIT.{md,json} — Numerical claim verification (always emitted at `assurance=submission`; `NOT_APPLICABLE` when no numeric claims; omitted in `draft` mode if Phase 5.5 detector was negative)
- paper/CITATION_AUDIT.{md,json} — Bibliography verification (always emitted at `assurance=submission`; `NOT_APPLICABLE` when no `.bib` or no `\cite{...}`; omitted in `draft` mode if Phase 5.8 detector was negative)
- paper/.ei/audit-verifier-report.json — External verifier report (submission only)

## Remaining Issues (if any)
- [items from final review that weren't addressed]

## Next Steps
- [ ] Visual inspection of PDF
- [ ] Add any missing manual figures
- [ ] Submit to [venue] via OpenReview / CMT / HotCRP
```

## Output Protocols

> Follow these shared protocols for all output files:
> - **[Output Versioning Protocol](../../shared-references/output-versioning.md)** — write timestamped file first, then copy to fixed name
> - **[Output Manifest Protocol](../../shared-references/output-manifest.md)** — log every output to MANIFEST.md
> - **[Output Language Protocol](../../shared-references/output-language.md)** — note: paper-writing always outputs English LaTeX for venue submission

## Key Rules

- **Large file handling**: If the Write tool fails due to file size, immediately retry using Bash (`cat << 'EOF' > file`) to write in chunks. Do NOT ask the user for permission — just do it silently.
- **Don't skip phases.** Each phase builds on the previous one — skipping leads to errors.
- **Checkpoint between phases** when AUTO_PROCEED=false. Present results and wait for approval.
- **Manual figures first.** If the paper needs architecture diagrams or qualitative results, the user must provide them before Phase 3.
- **Compilation must succeed** before entering the improvement loop. Fix all errors first.
- **Preserve all PDFs.** The user needs round0/round1/round2 for comparison.
- **Document everything.** The pipeline report should be self-contained.
- **Respect page limits.** If the paper exceeds the venue limit, suggest specific cuts before the improvement loop.

## Composing with Other Workflows

```
/idea-discovery "direction"         ← Workflow 1: find ideas
implement                           ← write code
/run-experiment                     ← deploy experiments
/auto-review-loop "paper topic"     ← Workflow 2: iterate research
/paper-writing "NARRATIVE_REPORT.md"  ← Workflow 3: you are here
                                         submit! 🎉

Or use /research-pipeline for the Workflow 1+2 end-to-end flow,
then /paper-writing for the final writing step.
```

## Typical Timeline

| Phase | Duration | Can sleep? |
|-------|----------|------------|
| 1. Paper Plan | 5-10 min | No |
| 2. Figures | 5-15 min | No |
| 3. LaTeX Writing | 15-30 min | Yes ✅ |
| 4. Compilation | 2-5 min | No |
| 5. Improvement | 15-30 min | Yes ✅ |

**Total: ~45-90 min** for a full paper from narrative report to polished PDF.
