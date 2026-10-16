# EvoInquiry in this research project

Merge the following rules into the project's AGENTS.md where they fit. For the
same preference across projects, use the AGENTS.md in your Codex home directory.
Retain existing instructions, resource limits, and workflow checkpoints.

The helper `python tools/configure_research_guidance.py --project /path/to/project`
manages only this guidance block. Use `--global` for your Codex home, `--dry-run`
to preview, `--check` to check the current block, or `--remove` to remove it.
Start a new Codex session after changing these instructions.

```markdown
On every research-related user turn, prefer a relevant installed EvoInquiry
skill and follow its applicable instructions before giving research advice or
performing research work. Select from the available names and descriptions using
the current request and conversation context; the user need not name a skill.
Honor an explicit skill choice. Use the execution skill directly for a clear
task; use evo-inquiry:research-guide when research routing or the next step is
unclear. Use another available skill when it better fits the requested work.

Short follow-ups, corrections, changed constraints, and "continue" / "继续"
inherit the active research task. Keep using its skill when it still fits; switch
when the requested work changes. When running the EvoInquiry Codex plugin, read
the selected SKILL.md and its research principles from the exact discovered
Codex path; resolve references beside that `skills/skills-codex/<name>/SKILL.md`
and do not substitute the sibling mainline `skills/<name>/` tree. Other
integrations should keep their own discovered skill and reference tree
consistent. Reuse guidance already
read and unchanged in this session; load only references needed for this task.
Briefly identify the skill actually used when answering a research request.

Apply the relevant research principles to advice, interpretation, planning,
implementation, and review. Reuse valid artifacts, check evidence behind resumed
statuses, and honor the workflow's review gates, resource limits, and stopping
conditions. Advice stays advice; a small edit stays a small edit. Skill selection
does not authorize experiments, purchases, external actions, or a full pipeline.
Greetings and unrelated tasks need no EvoInquiry workflow. If no suitable skill
is available, say so briefly and proceed within the requested scope. Follow
higher-priority instructions and the user's current constraints throughout.
```
