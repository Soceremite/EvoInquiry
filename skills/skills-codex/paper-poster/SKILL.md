---
name: paper-poster
description: "Deprecated poster entrypoint; redirects to paper-poster-html. Retained for existing calls. Use paper-poster-html for new conference posters."
argument-hint: "[paper-dir-or-pdf]"
allowed-tools: Read
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.
<!-- EVO-INQUIRY:END -->


# Paper Poster (DEPRECATED → /paper-poster-html)

This skill is retired. The LaTeX/tcbposter pipeline it described produced posters with
unbounded color palettes, no real paper figures, and no print-canvas verification, and
has been replaced by the measurement-gated HTML/CSS pipeline.

**Immediately proceed with `/paper-poster-html`**, passing through all of the user's
arguments unchanged. Do not attempt the legacy LaTeX flow.

The full legacy implementation remains available in git history
(`git log -- skills/skills-codex/paper-poster/SKILL.md`) if a venue ever mandates
LaTeX poster source — none is known to.
