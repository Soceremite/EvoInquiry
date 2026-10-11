# EvoInquiry agent guide

Full catalog: [skill catalog](docs/SKILLS_CATALOG.md) — **83 skills**.
Install and invoke the Codex plugin using [README.md](README.md).

The plugin discovers `skills/skills-codex/<name>/SKILL.md`. Read the selected
skill and its linked references before running the task. Its frontmatter,
workflow inputs, artifact contracts, and checkpoints define that task.
Project instructions and the user's authorization take precedence.

[Checkpoint controls](docs/CUSTOMIZATION.md) explain supervision and budgets;
[session recovery](docs/SESSION_RECOVERY_GUIDE.md) explains how to resume work.
[Backend compatibility](compatibility/codex-backends.md) covers optional services.
A fresh reviewer from the executor's model family is a provisional assessment;
it does not establish independent validation or research correctness.
