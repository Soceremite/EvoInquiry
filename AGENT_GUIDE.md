# EvoInquiry agent guide

Full catalog: [skill catalog](docs/SKILLS_CATALOG.md) — **86 skills** in the development tree:
83 retained workflows, research-guide, project-governance and environment-maintenance.
Install and invoke the Codex plugin using [README.md](README.md).

The plugin discovers `skills/skills-codex/<name>/SKILL.md`. Read the selected
skill and its linked references before running the task. Its frontmatter,
workflow inputs, artifact contracts, and checkpoints define that task.
Project instructions and the user's authorization take precedence.

Route clear natural requests directly to a relevant execution skill. Use
research-guide for resumed projects or an unclear next step across workflows.
Check the evidence behind resumed statuses, perform the requested work, and
continue necessary adjacent steps within the authorized goal and stopping point.
Small edits and advice-only requests retain their scope. This file is reference
documentation; merge the optional [project snippet](templates/EVOINQUIRY_AGENTS_SNIPPET.md)
into a research project's AGENTS.md to provide project-level instructions.

[Checkpoint controls](docs/CUSTOMIZATION.md) explain supervision and budgets;
[session recovery](docs/SESSION_RECOVERY_GUIDE.md) explains how to resume work.
[Backend compatibility](compatibility/codex-backends.md) covers optional services.
A fresh reviewer from the executor's model family is a provisional assessment;
it does not establish independent validation or research correctness.

Project state uses the shared .ei resolver. Read the
[upgrade implementation plan](docs/UPGRADE_IMPLEMENTATION_CN.md) for governance,
environment, code reuse and compatibility boundaries. Stable 1.0.0 installations
remain independent of this development checkout.
