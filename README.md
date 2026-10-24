# EvoInquiry

<picture>
  <source media="(prefers-reduced-motion: reduce)" srcset="docs/assets/evo-inquiry-hero.svg">
  <img src="docs/assets/evo-inquiry-hero.gif" alt="EvoInquiry: tiny researchers explore, test and learn in an evolving research loop" width="1440">
</picture>

[Static cover](docs/assets/evo-inquiry-hero.svg)

<p align="center">
  <a href="https://github.com/Soceremite/EvoInquiry/releases/tag/v1.6.1"><img src="https://img.shields.io/badge/release-1.6.1-FF927E?style=flat&amp;labelColor=7862E8" alt="Version 1.6.1"></a>
  <a href="docs/SKILLS_CATALOG.md"><img src="https://img.shields.io/badge/Codex_skills-89-59C7A7?style=flat&amp;labelColor=7862E8" alt="89 Codex skills"></a>
  <a href="https://github.com/Soceremite/EvoInquiry/actions/workflows/test-suite.yml"><img src="https://github.com/Soceremite/EvoInquiry/actions/workflows/test-suite.yml/badge.svg" alt="Regression test status"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-FFD95E?style=flat&amp;labelColor=7862E8" alt="MIT license"></a>
</p>

<p align="center">
  <strong>Research that evolves through evidence.</strong><br>
  <a href="README_CN.md">中文</a> · <a href="#installation">Quick start</a> · <a href="#capabilities">Skills</a> · <a href="https://github.com/Soceremite/EvoInquiry/releases">Releases</a> · <a href="CONTRIBUTING.md">Contribute</a>
</p>

Meet **EvoInquiry, a research companion that helps you take an idea forward.**

Research often starts with a single sentence. You read the papers, explore the
possibilities, and still need to work out what to try next. Once experiments are
running, there are resources to manage, results to interpret and failures to
understand. Bringing that work together into a convincing paper takes care at
every step.

We built EvoInquiry for Codex to help connect those steps. Its **89 Codex skills**
span brainstorming, literature search, experiment design, execution monitoring,
result analysis and paper writing. Evidence from one step becomes a useful input
for the next. Use one skill for a focused task, or connect them into a longer
workflow shaped by your research question, existing evidence and constraints.

We have put care into the details, too. Comparisons should account for data,
training budgets and random seeds. Analysis should examine concrete successes
and failures alongside the metrics. Long runs should include a plan for saving
weights, recovering from interruptions and keeping storage under control.

**Above all, we value objectivity.** Explain improvements clearly, report
regressions openly, and keep validating when the evidence is incomplete. A
research tool should help us see the problem more clearly.

**EvoInquiry 1.6.1 is open source.** Try it on your own research tasks and share
the problems and suggestions you encounter. Help us make this research companion
more dependable and more useful.

**New in [1.6.1](RELEASE_NOTES.md):** review after N complete experiments or
comparisons, with all planned methods, seeds and analysis counted as one group.
Healthy long training keeps running during ordinary reflection; normal monitoring
waits do not count as research stalls. Plan can observe existing jobs read-only
where the host supports it. Pending review holds the next launch, including
prepared jobs, while original resource limits and explicit STOP remain effective.
Use `problem-synthesis` when several unresolved problems may share an explanation.

## From a rough direction to an evidence-backed next step

Start with `scientific-brainstorming` to explore competing explanations and
feasible questions. Use `problem-synthesis` when several unresolved problems may
share a cause, and use `research-manager` to track decisions, unresolved issues
and handoffs in existing project records. Literature records
retain identity, versions and reading scope; figure receipts bind real inputs,
editable sources and captions. Existing comparison, checkpoint and review gates
remain in use. See [what changed](RELEASE_NOTES.md) and the
[1.6.1 validation record](docs/VALIDATION_1_6_1.md).

Try a bounded request such as “Frame research questions about low-cost memory;
no training yet”, “Check whether these means support the claim”, or “Plot this
CSV and retain the script, missing runs and uncertainty definition”. A complete
pipeline is available when requested.

## What makes EvoInquiry useful

| Design choice | What it means for your research |
| --- | --- |
| **Evidence guides the next step** | Resume from verified artifacts, expose unresolved questions and revise a method as results arrive. |
| **Comparisons match the question** | Separate mechanism contribution, equal-resource performance and tuned-system performance; account for seeds, failures and uncertainty. |
| **Claims stay connected to results** | Audit experiments, challenge alternative explanations and check paper claims against raw evidence. |
| **Long runs respect resources** | Budget saving peaks, keep bounded recovery points and retain useful model dependencies alongside the experiment record. |

## A research workflow that can change direction

![Research workflow: discover, refine, plan, run, audit and write, with feedback into the method and the next question](docs/assets/research-loop.svg)

`research-pipeline` connects the full lifecycle. For a clear task, use its execution
skill directly; `research-guide` coordinates continuation when the stage is unclear.
Plans, raw results and review reports remain useful inputs for the next step.
Your scope, review gates, resource budget and stopping conditions govern the work.

<a id="installation"></a>

## Quick start

Download and extract `evo-inquiry-1.6.1.tar.gz` or `.zip` from the
[stable release](https://github.com/Soceremite/EvoInquiry/releases/tag/v1.6.1).
Assets become available after the version's publication checks pass.
Use a Codex version with the `codex plugin` commands; installation has been checked
with Codex CLI **0.163.0** on Linux.

```sh
cd /path/to/evo-inquiry-1.6.1
codex plugin marketplace add "$PWD"
codex plugin add evo-inquiry@evo-inquiry
```

Start a **new Codex session**, provide your project materials and ask for a task:

> Refine this research idea into a focused, implementable method proposal.
> Use this project's related work and identify the unresolved question.

> Design a fair comparison for this method: data splits, strong baselines,
> training and tuning budgets, seed strategy, evaluation and failure accounting.

> Use `evo-inquiry:analyze-results` to summarise these CSV files across seeds.
> Save the comparison table and stop after the analysis.

Skills appear under the `evo-inquiry:` namespace. Plugin installation makes them
available; persistent selection preferences are [configured separately](#usage).

<details>
<summary><strong>Source development and a clean installation</strong></summary>

For source development, use
`git clone --branch v1.6.1 https://github.com/Soceremite/EvoInquiry.git EvoInquiry`.
Install the plugin from a clean release archive. Codex CLI 0.162.1 copies local
untracked files too, so a release archive keeps private validation records,
build outputs and Git history out of the installed cache.

</details>

## Fair comparisons, by design

![Fair comparison design: shared data and evaluation boundaries, then controlled contribution, equal resource budget or tuned performance](docs/assets/fair-comparison.svg)

Choose the comparison question first. Declare common data and evaluation settings
once, then explain justified method-specific differences. Use strong relevant
baselines, validation-based selection and held-out evaluation.

Replication follows observed variability, useful precision and budget. Report
individual runs, failures and deviations alongside aggregates and uncertainty.
The design determines whether a result supports a mechanism claim, a resource-bound
comparison or tuned-system performance.

Planning → implementation → execution → analysis → review share the same
[comparison guidance](skills/shared-references/comparative-experiments.md).

## Preserve evidence, control storage

![Comparison archival: verify the protocol, configurations and all attempt evidence before retaining selected weights and complete records](docs/assets/evidence-archive.svg)

Long-running experiments include a storage budget and bounded checkpoint retention.
The default keeps **two valid recovery points**, a validation-selected best model
and a final model when required. Plans include concurrent save peaks; implementation
and monitoring check actual saving and recovery.

When training finishes or is explicitly ended, validated inference weights allow
unused recovery states to be released. Completed comparison groups prefer the
validation-selected winner's weights, while protecting planned model dependencies
and **every run's evidence, including failed attempts**.

The optional local helper checks declared coverage and fixed file hashes before
comparison consolidation. Research review assesses the comparison's fairness and
claim support. See the [storage policy](skills/skills-codex/shared-references/experiment-storage.md)
and [comparison evidence format](docs/COMPARISON_EVIDENCE.md).

<a id="capabilities"></a>

## Explore the toolkit

| Capability | Tasks | Example skills |
| --- | --- | --- |
| Project continuation | Reuse existing evidence and coordinate the next authorized step | `research-guide` |
| Research decisions and handoffs | Track evidence, competing options, blockers and authorized next steps | `research-manager` |
| Project and evidence governance | Fix inputs and execution identities, recover reports and plan migrations | `project-governance` |
| Environment maintenance | Validate candidates and protect environments needed for reproduction | `environment-maintenance` |
| Literature and knowledge | Search papers, map prior work, check novelty and maintain a knowledge base | `research-lit`, `novelty-check`, `research-wiki` |
| Ideas and research design | Frame vague directions, explore alternatives, refine a method and plan tests | `scientific-brainstorming`, `idea-discovery`, `research-refine`, `experiment-plan` |
| Theory and proofs | Organize assumptions, derive formulas, write proofs and check gaps | `formula-derivation`, `proof-writer`, `proof-checker` |
| Experiments and analysis | Implement comparisons, run experiments, analyse seeds and plan ablations | `experiment-bridge`, `run-experiment`, `analyze-results` |
| Evidence and review | Audit integrity, assess supported claims, verify citations and challenge conclusions | `experiment-audit`, `result-to-claim`, `research-review` |
| Papers and figures | Develop an outline, draft LaTeX, generate figures and compile a paper | `paper-plan`, `paper-writing`, `paper-figure` |
| Talks and submissions | Prepare slides and posters, respond to reviews and adapt a paper for resubmission | `paper-talk`, `paper-poster-html`, `rebuttal` |
| Proposals and patents | Organize funding proposals and draft patent application materials | `grant-proposal`, `patent-pipeline` |

Primarily built for ML, AI and related engineering research. See the
[full skill inventory](docs/SKILLS_CATALOG.md) for domain-specific workflows,
orchestrators and optional provider backends.

Version 1.4.0 makes [case studies](skills/skills-codex/shared-references/case-study-analysis.md)
part of substantive result analysis: inspect existing sample outputs, explain
concrete improvements and failures, and retain traceable, fairly paired examples.
Classification errors, regression residuals, generated images and timestamped
video evidence use task-appropriate displays. Short metric queries stay short;
missing sample outputs are reported rather than invented. New inference or
experiments require their own scope and resource authorization.

<a id="usage"></a>

## Use EvoInquiry throughout a project

Version 1.5.0 adds bounded continuation: keep the original task clock, reserve
resources before dispatch, reconcile interrupted actions and check the handoff
against current sources. Reuse valid reviewed work and choose the next wave from
its evidence; a negative finding or justified stop can complete the task.
See the [Plan/Goal usage guide (Chinese)](docs/BOUNDED_RESEARCH_CN.md) and
[validation record](docs/VALIDATION_1_5_0.md). Plan and Goal remain optional host
features; EvoInquiry does not automatically create a Goal or a background service.

> Continue this research project from its existing proposal and pilot results.
> Complete the next useful analysis and prepare the follow-up plan; stop before
> launching new experiments.

Small edits and advice-only requests keep their scope. You can name any skill
explicitly. For an end-to-end task, ask for `evo-inquiry:research-pipeline` with your
research direction, existing work, target output, and available resources.

<details>
<summary><strong>Prefer EvoInquiry on every research turn</strong></summary>

To prefer EvoInquiry on every research turn, add persistent routing instructions.
The optional [AGENTS.md snippet](templates/EVOINQUIRY_AGENTS_SNIPPET.md) covers
direct skill selection, short follow-ups, changes of task, and applying research
principles to advice as well as execution. Previously loaded, unchanged guidance
can be reused; a follow-up does not need a fresh full-file read to use a skill.

From this source checkout, use the helper below for one research project:

```sh
python tools/configure_research_guidance.py --project /path/to/project --dry-run
python tools/configure_research_guidance.py --project /path/to/project
```

Use `--global` instead of `--project /path/to/project` to apply the same research
preference across projects. The helper preserves other instructions, updates the
active AGENTS.override.md when present, and supports `--check` and `--remove`.
Start a new Codex session afterward. Plugin installation makes skills available;
it does not automatically install these persistent preferences. Automatic
selection remains model-dependent, and explicit user instructions take priority.

</details>

<details>
<summary><strong>Workflow checkpoints and session recovery</strong></summary>

Workflow checkpoint settings let you choose how closely to supervise a run.
With `AUTO_PROCEED=true`, authorized work continues in the same turn after
reporting the selected path. An explicitly blocking checkpoint requires a
reply; `AUTO_PROCEED=false` enables blocking feedback checkpoints. Project
instructions and resource limits apply throughout. See [workflow controls](docs/CUSTOMIZATION.md)
and [session recovery](docs/SESSION_RECOVERY_GUIDE.md).

</details>

<a id="setup"></a>

## Setup and validation

Search services, external reviewers, GPU platforms, image renderers, and LaTeX
tooling need their own dependencies and, where applicable, credentials.
Configure the services you intend to use; see
[backend setup and compatibility](compatibility/codex-backends.md).

The documented EvoInquiry installation route is the Codex plugin above.
Retained backend and client compatibility resources support existing workflow
contracts; they are optional and have separate setup requirements.

Current checks and their scope are recorded in [1.6.1 validation](docs/VALIDATION_1_6_1.md).
The patch passed 304 focused local tests, including three real CPU comparison
blocks and live-worker observation/stop checks. Native Goal/Plan session behavior
is not established by these tests. In the earlier [1.6.0 validation](docs/VALIDATION_1_6_0.md),
1,349 tests passed and a real one-hour CUDA engineering
run checked bounded recovery storage and numerical fault handling. A separate
bounded native-model observation exercised REPLAN, actual STOP delivery to a
running CUDA job and full-state replay. Failed attempts and control regressions
remain recorded. These constructed, guided checks do not establish general
superiority, an always-on watchdog or unattended scientific discovery over hours
or days. The earlier [1.5.0 practical validation](docs/VALIDATION_1_5_0.md) remains available.
The earlier [1.4.0 publication](docs/VALIDATION_1_4_0.md) remains a separate record.
Historical evidence remains in [governance validation](docs/UPGRADE_VALIDATION_CN.md)
and [portability coverage](docs/PORTABILITY_VALIDATION_CN.md).
The [offline behavior evaluation](docs/SKILL_BEHAVIOR_EVAL.md) compares natural
requests using frozen fixtures and actual execution traces. Release archives
require passing Linux and macOS full CI suites and native Windows installer/governance checks with both `powershell.exe` and `pwsh`.
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

<details>
<summary><strong>Upgrade, switch sources or roll back</strong></summary>

Update from EvoInquiry releases. Keep the source checkout available: Codex
loads an installed cache, so changes require refreshing the plugin and
starting a new session. Re-register the local marketplace if you move the
checkout to a different path.

To switch versions or move the source, enter the clean extracted release directory and replace the existing marketplace source before reinstalling:

```sh
codex plugin marketplace remove evo-inquiry
codex plugin marketplace add "$PWD"
codex plugin add evo-inquiry@evo-inquiry
```

Start a new session and keep the selected source directory available. These commands also support rollback from a preserved prior release directory; switching the plugin does not migrate project state. See the [deployment guide](docs/DEPLOYMENT_GUIDE.md) for storage probes, durable project placement, backup boundaries and verified source switching.

</details>

README diagrams are local, editable SVGs; the cover also has a lightweight GIF
with gentle character animation. See the [visual sources](docs/assets/README.md)
to rebuild the images with EvoInquiry's own `figure-spec` and `pixel-art` workflows.

<a id="license"></a>

## License and acknowledgments

MIT licensed. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
EvoInquiry builds on research workflow tools from
[ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep).
