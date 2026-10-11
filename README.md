# EvoInquiry

**Research that evolves through evidence.**

[中文](README_CN.md) · [Skill inventory](SKILL_AUDIT_CN.md) · [Releases](https://github.com/Soceremite/EvoInquiry/releases) · [Contributing](CONTRIBUTING.md)

**1.0 Beta — `v1.0.0-beta.2`**

EvoInquiry is a research workflow toolkit for Codex. Its **83 Codex skills**
help you turn a broad research direction into a focused proposal, implement
and evaluate experiments, assess the evidence, and prepare a paper for
submission. Use individual skills for a specific task or connect them into
a longer research workflow.

## What you can do

| Capability | Tasks | Example skills |
| --- | --- | --- |
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

The current beta primarily targets ML, AI, and related engineering research.
Domain-specific workflows and provider integrations are available in the
[full inventory](SKILL_AUDIT_CN.md); choose those that fit your project.

## Install

Use a Codex installation that provides the `codex plugin` commands. Plugin
installation has been checked with Codex CLI **0.162.1** on Linux.

```sh
git clone --branch v1.0.0-beta.2 https://github.com/Soceremite/EvoInquiry.git EvoInquiry
cd EvoInquiry
codex plugin marketplace add "$PWD"
codex plugin add evo-inquiry@evo-inquiry
```

You can also extract a [release archive](https://github.com/Soceremite/EvoInquiry/releases),
enter its root directory, and run the two `codex plugin` commands. Start a
new Codex session after installation. Skills appear under the `evo-inquiry:`
namespace, for example `evo-inquiry:research-refine`.

## Start with a task

Give Codex the relevant project context and ask for the skill you need:

> Use `evo-inquiry:research-refine` to turn this research direction into a
> focused proposal. Identify the closest prior work, the unresolved problem,
> and the evidence needed to test the method.

> Use `evo-inquiry:experiment-plan` to design experiments for this proposal.
> Include baselines, evaluation criteria, ablations, and failure conditions.

> Use `evo-inquiry:result-to-claim` to analyze these raw experiment results.
> Explain which claims they support and which questions remain unresolved.

> Use `evo-inquiry:paper-writing` to prepare a paper from this narrative
> report and the supporting results. Target the venue specified in the project.

For an end-to-end task, ask for `evo-inquiry:research-pipeline` and provide your
research direction, existing work, target output, and available resources.
The beta installs all 83 entrypoints, including individual steps, pipeline
orchestrators, and optional provider backends.

Workflow checkpoint settings let you choose how closely to supervise a run.
With `AUTO_PROCEED=true`, authorized work continues in the same turn after
reporting the selected path. An explicitly blocking checkpoint requires a
reply; `AUTO_PROCEED=false` enables blocking feedback checkpoints. Project
instructions and resource limits apply throughout.

## Setup and beta status

Search services, external reviewers, GPU platforms, image renderers, and LaTeX
tooling need their own dependencies and, where applicable, credentials.
Configure the services you intend to use; see
[backend setup and compatibility](compatibility/codex-backends.md).

The documented EvoInquiry installation route is the Codex plugin above.
Additional client packages and setup resources are included for reference;
they have separate compatibility requirements.

The previous beta passed **777 tests with 20 skips**, and its full Linux and
macOS CI suites passed. Current releases run those CI suites before publishing
archives. See [validation scope and limitations](docs/BETA_VALIDATION.md).
Live providers and complete research projects have not been verified end to
end across every environment or discipline.

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

## License and acknowledgments

MIT licensed. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
EvoInquiry builds on research workflow tools from
[ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep).
