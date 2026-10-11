# Beta validation scope

Release: **1.0.0-beta.3**. Upstream snapshot:
`3b19a22dc5a64c983d2eafd6c2c94000fadc4f8d`.

## Checked for this release

- Local Linux regression suite: **779 passed, 20 skipped**, Python 3.12.14.
- Focused packaging and workflow checks: 35 passed. After strengthening the
  archive's required-reference check, all 5 publication tests passed again.
- 83 Codex skill bodies and frontmatter match the pinned upstream snapshot
  after removing only the marked EvoInquiry hook. Retained runtime helpers,
  references, templates, and reviewer overlays remain unchanged.
- All previously tracked files were reviewed; 485 text documents were read.
  193 promotional, duplicated, or unrelated files were removed. Required
  tutorial examples and compatibility resources were retained.
- Local links in the revised public guides resolve. Retained Markdown has no
  links to the deleted materials.
- The publication policy rejects retired files and missing workflow references,
  including an existing reference omitted from the archive's tracked-file list.
- Linux and macOS full suites must pass in GitHub Actions before release assets
  are published. The actual Actions results define their status.

The 20 local skips consist of 12 Windows PowerShell checks, 4 credential-gated
MiniMax live checks, and 4 installer/picker checks requiring `expect`.

## Existing installation evidence

A Codex CLI 0.162.1 session discovered the EvoInquiry namespace and all 83
entrypoints during beta development, then read an installed entrypoint and
its shared reference. Principle links also resolved after relocating the
package into a directory with spaces. These checks establish packaging and
discovery, not research outcomes.

Release-specific evidence is summarized in
[release-validation.json](../release-validation.json).

## Limits

The workflows primarily target ML, AI, and related engineering research.
Live providers, GPUs, image renderers, complete research projects, Windows,
and broad discipline coverage have not been verified end to end for this beta.
Same-family agent review remains provisional. Automated review scores and
synthetic exercises do not establish research correctness or general quality
improvements. Local raw session records are excluded from public Git content.
