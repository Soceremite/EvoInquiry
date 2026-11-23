# Rebuttal upstream and migration

EvoInquiry 1.7.0 uses [awesome-rebuttal at 3434455](https://github.com/xiongqi123123/awesome-rebuttal/tree/3434455fb2460b85793b4e3082bd28bf86ff7323).
The vendored capabilities, JSON schemas, source template and renderer carry the
upstream MIT license. The template keeps its author-kit attribution. Build the
example PDF from the template source when needed.

The first sync retained upstream capability and schema paths. To replay,
compare the pinned source with `skills/rebuttal/`. Replace the upstream runtime
path in Markdown with the EvoInquiry state directory `.ei/rebuttal/` and replay
the entrypoint's existing governance blocks, frontmatter and the explicitly
marked `EI-LOCAL` sections. The installed Codex surface follows the same
workflow through its own linked references.

| Previous workflow | Current owner |
| --- | --- |
| Normalize and atomize reviews, ISSUE_BOARD, strategy | Capabilities 01 and 05–08. Keep raw anchors, concern IDs and the response matrix in memory |
| Supplemental experiments | Capability 10 with stable EXP IDs, triage and optional authorized experiment-bridge handoff |
| Drafts and PASTE_READY | Capabilities 11–13. Exact venue limits, six response formats, optional rich drafts and AC summary |
| Provenance, commitments, coverage, consistency and limits | Capability 14 and the exact-artifact CLI. Capability 20 tracks REVISION_PLAN in both directions |
| External stress test | Capability 18 defaults to in-context personas. Optional external reviewers retain model identity, trace and round limits |
| Follow-up discussion | Capability 19 retains raw anchors, engagement and score history, then produces delta replies |
| Progress and rendered views | Snapshots and PDF support. Use render-html separately when requested |

The legacy entrypoints are retained under [docs/archive/rebuttal-legacy](archive/rebuttal-legacy/)
and at the local tag `rebuttal-legacy`. If a project has the old `rebuttal/`
directory, choose read-only continuation or explicitly map the existing
review, strategy and checklist records into the new memory format. Keep the
original source references and checked items. Start the updated workflow with
the project and venue rules already supplied by the author.
