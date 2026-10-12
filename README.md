# EvoInquiry

**Research that evolves through evidence.**

[中文](README_CN.md) · [Skill inventory](docs/SKILLS_CATALOG.md) · [Releases](https://github.com/Soceremite/EvoInquiry/releases) · [Contributing](CONTRIBUTING.md)

**1.0 Beta — `v1.0.0-beta.5` candidate**

EvoInquiry is a research workflow toolkit for Codex. Its **84 Codex skills**
help you turn a broad research direction into a focused proposal, implement
and evaluate experiments, assess the evidence, and prepare a paper for
submission. Use individual skills for a specific task or connect them into
a longer research workflow.

<a id="capabilities"></a>

## What you can do

| Capability | Tasks | Example skills |
| --- | --- | --- |
| Project continuation | Reuse existing evidence, resolve the current uncertainty, and coordinate the next authorized step | `research-guide` |
| Literature and knowledge | Search papers, map related work, check novelty, and maintain a research knowledge base | `research-lit`, `novelty-check`, `research-wiki` |
| Ideas and research design | Explore directions, refine a method, and plan experiments around testable claims | `idea-discovery`, `research-refine`, `experiment-plan` |
| Theory and proofs | Organize assumptions, derive formulas, write proofs, and check gaps | `formula-derivation`, `proof-writer`, `proof-checker` |
| Experiments and analysis | Implement experiments, launch jobs, monitor progress, analyze results, and plan ablations | `experiment-bridge`, `run-experiment`, `analyze-results` |
| Evidence and review | Audit experimental integrity, assess supported claims, verify citations, and challenge conclusions | `experiment-audit`, `result-to-claim`, `research-review` |
| Papers and figures | Develop an outline, draft LaTeX, generate figures, and compile a paper | `paper-plan`, `paper-writing`, `paper-figure` |
| Talks and submissions | Prepare presentations and posters, respond to reviews, and adapt a paper for resubmission | `paper-talk`, `paper-poster-html`, `rebuttal` |
| Proposals and patents | Organize funding proposals and draft patent application materials | `grant-proposal`, `patent-pipeline` |

For a complete workflow, `research-pipeline` connects direction discovery,
experiments, review, and paper preparation. Intermediate plans, results,
review reports, and research notes give you concrete artifacts to inspect
and carry into the next stage. Review cycles let you revise a proposal or
method as new evidence arrives.

Long-running experiments include a storage budget and bounded checkpoint
retention. The default keeps two valid training recovery points, a
validation-selected best model, and a final model when required. Plans account
for concurrent save peaks and completed runs; implementation and monitoring
check actual saving and recovery. When training finishes or is explicitly ended,
unused recovery states can be released after validated weights are saved.
Completed comparison groups prefer the validation-selected winner's weights,
with planned model dependencies and every run's evidence preserved.
See the [storage policy](skills/skills-codex/shared-references/experiment-storage.md)
for native framework integration and the optional local checkpoint helper.

The current beta primarily targets ML, AI, and related engineering research.
Domain-specific workflows and provider integrations are available in the
[full inventory](docs/SKILLS_CATALOG.md); choose those that fit your project.

<a id="installation"></a>

## Install

Use a Codex installation that provides the `codex plugin` commands. Plugin
installation has been checked with Codex CLI **0.162.1** on Linux.

For this candidate, enter its local checkout or extracted candidate archive and
run the two plugin commands below:

```sh
cd /path/to/EvoInquiry
codex plugin marketplace add "$PWD"
codex plugin add evo-inquiry@evo-inquiry
```

After publication, obtain this version with
`git clone --branch v1.0.0-beta.5 https://github.com/Soceremite/EvoInquiry.git EvoInquiry`.

You can also extract a [release archive](https://github.com/Soceremite/EvoInquiry/releases),
enter its root directory, and run the two `codex plugin` commands. Start a
new Codex session after installation. Skills appear under the `evo-inquiry:`
namespace, for example `evo-inquiry:research-refine`.

<a id="usage"></a>

## Start with a task

Give Codex the relevant files, goal, and constraints. Natural requests let it
select a matching skill:

> Refine this research idea into a focused, implementable method proposal.
> Use the related work in this project and identify the unresolved problem.

> Design experiments for this fixed proposal.
> Include baselines, evaluation criteria, ablations, and failure conditions.

> Assess which claims these raw results support and which evidence is missing.

> Continue this research project from its existing proposal and pilot results.
> Complete the next useful analysis and prepare the follow-up plan; stop before
> launching new experiments.

Clear tasks go directly to the corresponding skill. `research-guide` coordinates
continuation when the stage is unclear or spans workflows. It checks existing
evidence, reads the selected execution skill, performs the authorized work, and
honors its review gates and stopping conditions. Small edits and advice-only
requests retain their scope. You can still name any skill explicitly, for example:

> Use `evo-inquiry:analyze-results` to summarize these CSV files across seeds.
> Save the comparison table and stop after the analysis.

For an end-to-end task, ask for `evo-inquiry:research-pipeline` and provide your
research direction, existing work, target output, and available resources.
The beta installs 83 retained workflow entrypoints plus `research-guide`,
including individual steps, pipeline orchestrators, and optional backends.

For project-wide research guidance, merge the optional
[AGENTS.md snippet](templates/EVOINQUIRY_AGENTS_SNIPPET.md) into your research
project's instructions. Keep its existing rules and limits. Installation alone
does not load this repository's AGENT_GUIDE.md into other projects.

Workflow checkpoint settings let you choose how closely to supervise a run.
With `AUTO_PROCEED=true`, authorized work continues in the same turn after
reporting the selected path. An explicitly blocking checkpoint requires a
reply; `AUTO_PROCEED=false` enables blocking feedback checkpoints. Project
instructions and resource limits apply throughout. See [workflow controls](docs/CUSTOMIZATION.md)
and [session recovery](docs/SESSION_RECOVERY_GUIDE.md).

<a id="setup"></a>

## Setup and beta status

Search services, external reviewers, GPU platforms, image renderers, and LaTeX
tooling need their own dependencies and, where applicable, credentials.
Configure the services you intend to use; see
[backend setup and compatibility](compatibility/codex-backends.md).

The documented EvoInquiry installation route is the Codex plugin above.
Retained backend and client compatibility resources support existing workflow
contracts; they are optional and have separate setup requirements.

Candidate checks and their status are recorded in [validation scope and limitations](docs/BETA_VALIDATION.md).
The [offline behavior evaluation](docs/SKILL_BEHAVIOR_EVAL.md) compares natural
requests using frozen fixtures and actual execution traces. Release archives
require passing Linux and macOS CI suites.
Live providers and complete research projects have not been verified end to
end across every environment or discipline.

<a id="contributing"></a>

## Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md). To check a local checkout:

```sh
python -m pip install -r requirements-dev.txt
python tools/verify_evo_inquiry.py
python tools/check_skills_inventory.py
python -m pytest tests/ -q
```

Update from EvoInquiry releases. Keep the source checkout available: Codex
loads an installed cache, so changes require refreshing the plugin and
starting a new session. Re-register the local marketplace if you move the
checkout to a different path.

To roll back, enter a beta.3 checkout or extracted release and repeat the two
installation commands, then start a new session. Repeat them from the candidate
directory to restore beta.5. Keep the selected source directory available.

<a id="license"></a>

## License and acknowledgments

MIT licensed. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
EvoInquiry builds on research workflow tools from
[ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep).
