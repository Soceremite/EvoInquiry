# Beta validation scope

Release: 1.0.0-beta.1. Upstream snapshot:
`3b19a22dc5a64c983d2eafd6c2c94000fadc4f8d`.

## Completed checks

- The release-source full repository suite passed 777 tests with 20 skips
  on Linux x86_64, Python 3.12.14 (275.03 seconds).
- The skip inventory includes 12 Windows PowerShell tests, 4 credential-gated
  MiniMax live tests, and 4 interactive installer/picker tests.
- All 83 Codex entrypoints retain their upstream frontmatter and workflow
  bodies after removing the added, explicitly marked EvoInquiry hook.
- Other retained client/ reviewer overlay files are unchanged. The Claude
  overlay generator strips the Codex-only hook when regenerating its overlay.
- A fresh Codex CLI 0.162.1 session discovered the evo-inquiry namespace and
  all 83 entrypoints, then read an installed entrypoint and its shared principles.
- Relative principle references resolved after relocating the package to a
  different directory with spaces.
- Codex compatibility links resolved and the MCP TOML template parsed.
- Synthetic research discussion and nested-review exercises were performed
  during development. They have no randomized baseline comparison and do not
  establish a general improvement in research outcomes.

Release-specific checks are summarized in
[release-validation.json](../release-validation.json). CI reruns the repository
tests; platform support follows observed results rather than the existence
of a workflow file.

## Limits

The inherited workflows mainly target ML/AI and related engineering research.
The principles are general, but broad discipline support is untested.
Live third-party providers, image renderers, GPUs, full research pipelines,
and every operating system have not been verified end to end for this beta.
An automated review score is not evidence that a research claim is true.
Original local installation records and raw session logs are excluded from
public Git content; they are not required to install the plugin.
