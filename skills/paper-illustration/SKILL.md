---
name: paper-illustration
description: "Generate publication-quality AI illustrations for academic papers using Gemini image generation. Creates architecture diagrams, method illustrations with Claude-supervised iterative refinement loop. Use when user says \"生成图表\", \"画架构图\", \"AI绘图\", \"paper illustration\", \"generate diagram\", or needs visual figures for papers."
argument-hint: "[description-or-method-file] [— style-ref: <source>]"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, mcp__codex__codex, mcp__codex__codex-reply, WebSearch
---

<!-- EVO-INQUIRY:BEGIN -->
For research work, read [EvoInquiry](../shared-references/evo-inquiry.md),
or reuse it if already loaded and unchanged in this session. Apply relevant
principles within the user's scope and this skill's existing outputs, review
standards, and recovery contracts. Carry them into nested research tasks and
reviewer briefs. Continue authorized work through its necessary steps; honor
budgets, blocking checkpoints, and stopping conditions.
<!-- EVO-INQUIRY:END -->


<!-- EI-GOVERNANCE:BEGIN -->
Resolve runtime state through tools/state_paths.py before .ei operations. Use
[project-governance](../shared-references/project-governance.md) for fixed evidence,
profiles and controlled migration; missing profiles retain compat-v1.
<!-- EI-GOVERNANCE:END -->


# Paper Illustration: Multi-Stage Claude-Supervised Figure Generation

Confirm the figure purpose and input method. Follow the applicable prompt, rendering, and quality review stages. Use the existing provider and output rules for the selected host.

## Workflow references

Use the applicable stages in order. Load the referenced instructions when the stage is needed.

- [Core Design Philosophy through What to AVOID (CRITICAL)](references/workflow-01-core-design-philosophy.md)
- [Scope through Step 2: Gemini Layout Optimization (gemini-3-pro)](references/workflow-02-scope.md)
- [Step 3: Gemini Style Verification (gemini-3-pro) through Step 4: Paperbanana Image Rendering (gemini-3-pro-image-preview)](references/workflow-03-step-3-gemini-style-verification-gemini-3-pro.md)
- [Step 5: Claude STRICT Visual Review & Scoring (MANDATORY) through Key Rules (MUST FOLLOW - STRICT)](references/workflow-04-step-5-claude-strict-visual-review-scoring-mandatory.md)
- [Output Structure through Model Summary](references/workflow-05-output-structure.md)
