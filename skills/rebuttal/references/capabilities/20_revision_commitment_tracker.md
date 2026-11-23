<!-- EI-LOCAL:BEGIN -->
# 20 Revision commitment tracker

Read during drafting, final safety review, and follow-up edits. Keep
`drafts/REVISION_PLAN.md` in the existing rebuttal workspace. Each checklist item
has a stable ID, one concern ID, a paper location, an atomic edit, its approval
classification and a completion checkbox. Group the same items by section and
severity, count each classification, and log excluded concerns and reasons.
Use the [template](../templates/revision_plan.md). Update IDs and completed
checkboxes in place across discussion rounds.

Before drafting, save the confirmed `memory/venue_rules.json` using the upstream
schema and run `python <package>/tools/rebuttal_check.py --root <project> --check intake`.
For finalization, save `memory/submission-check.json` in the same workspace.

| Field | Records |
| --- | --- |
| `concerns` | Objects with `id`, `reviewer`, `status` and a `reason` for `deferred_intentionally`. Derive these from the complete concern ledger |
| `drafts` | Project-relative `path`, optional thread `reviewer`, and ordered `units` whose joined `text` equals the exact output |
| `units` | `kind` of `fact`, `commitment` or `framing`, `text`, linked `concerns`, and `sources` for facts. A promise carries a `commitment` revision ID |
| `sources` | Each object has `ref` with project-relative `path` and `sha256`, and the verbatim `excerpt`. Verify its semantic support for the claim |
| `revisions` | `id`, `concern_id`, `status` and `evidence`, with the same source format for author approval or completion |
| `rehearsal` | Optional `backend`, `executor_model` and `external_rounds` with `reviewer_model`, `identity_verified`, and the fixed `response_ref` |
| `pdf` | For a PDF, include its fixed `ref` and measured `pages` from the compiled artifact. Include the checked LaTeX in `drafts` |

The author classifies commitments as `already_done`, `approved_for_rebuttal`, or
`future_work_only`. Future work remains conditional. For finalization, each
approved or completed checklist item must appear in the response ledger, and
each paper-edit promise must map to an approved item. Carry excluded items into
the out-of-scope log with their reason. Any draft edit requires another check.

Run `python <package>/tools/rebuttal_check.py --root <project> --check finalize --record`
after checking the substance, evidence, cross-reply consistency and tone.
The command checks the exact artifacts, claims ledger, and revision links.
Use the independent semantic safety checklist before delivering submission text.
<!-- EI-LOCAL:END -->
