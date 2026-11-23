<!-- EI-WORKFLOW-REFERENCE -->

# Thread independence

Read this file when the workflow reaches Thread independence through Example Invocations. In commands and examples, interpret relative skill paths from the entrypoint directory.

### Thread independence

Every **top-level** `/proof-checker` invocation starts a fresh reviewer thread. For codex this is `mcp__codex__codex`; for manual this is `mcp__manual_review__review`. Do not reuse a saved threadId across separate invocations of this skill. Within a single top-level invocation, the appropriate reply tool (`mcp__codex__codex-reply` or `mcp__manual_review__review_reply`) threads the Phase 3 follow-up rounds — the reviewer needs prior-issue context to judge whether a fix actually closed the gap, and the Phase 1→3 flow above explicitly relies on this. The Phase 3.5 "Independent second review for FATAL/CRITICAL fixes" sub-step is the deliberate exception inside a single run: it must spawn a fresh thread so the blind reviewer has no exposure to the original critique.

Do not accept prior audit outputs (PAPER_CLAIM_AUDIT, CITATION_AUDIT, EXPERIMENT_LOG) as input across separate invocations — the cross-run freshness is what preserves reviewer independence per `shared-references/reviewer-independence.md`.

This skill never blocks by itself; `paper-writing` Phase 6 plus the
verifier decide whether the verdict blocks finalization based on the
`assurance` level.

## Example Invocations

```
/proof-checker "neurips_2025.tex"
/proof-checker "check the GMM generalization proof, focus on dimension dependence"
/proof-checker "verify proof in paper.tex — difficulty: nightmare"
/proof-checker "paper/main.tex --deep-fix"            # opt-in: ask reviewer to also emit repair-grade deep_fix_plans
/proof-checker "paper/main.tex --restatement-check"   # opt-in: run Phase 3.6 to detect cross-location theorem-statement drift
/proof-checker "paper/main.tex --deep-fix --restatement-check"   # both opt-ins, independent
```
