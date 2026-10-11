# EvoInquiry

**Research that evolves through evidence.**

[中文](README_CN.md) · [Research principles](skills/skills-codex/shared-references/evo-inquiry.md) · [Skill inventory](SKILL_AUDIT_CN.md) · [Changelog](CHANGELOG.md)

**1.0 Beta — `v1.0.0-beta.1`**

EvoInquiry combines **83 Codex skills** inherited from
[ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep)
with six shared research principles. It supports literature discovery, idea
refinement, experiments, research review, proofs, and paper writing while
keeping conclusions proportional to the evidence.

The principles are Independent Judgment, Grounded Inquiry, Explanatory
Simplicity, Discriminating Research, Honest Conclusions, and Reflective
Progress. Each research skill reads the relevant guidance, including in
nested research tasks and reviewer briefs. Project-specific constraints
continue to apply. The principles do not set universal compute budgets or
grant permission for additional actions.

## Install the beta

Tested with Codex CLI **0.162.1** on Linux. Use a Codex installation that
provides the `codex plugin` commands.

Clone the beta tag, then register the repository as a local marketplace:

```sh
git clone --branch v1.0.0-beta.1 https://github.com/Soceremite/EvoInquiry.git evo-inquiry
cd evo-inquiry
codex plugin marketplace add "$PWD"
codex plugin add evo-inquiry@evo-inquiry
```

Alternatively, extract the release archive, enter its root directory, and run
the two `codex plugin` commands. Start a new Codex session. Its skill catalog
should expose names such as `evo-inquiry:research-refine`.

Users already running ARIS or the earlier Lyd's Compass prototype should
disable that earlier plugin when enabling EvoInquiry, so only the intended
edition is active. Preserve the earlier package for rollback. The installed
cache is separate from this checkout; source edits require reinstalling or
refreshing the plugin and starting a new session.

## Use it

Ask Codex to use the namespaced skill for your task, for example:

> Use `evo-inquiry:research-refine` to turn this research direction into a
> focused proposal. Distinguish assumptions, existing evidence, and unknowns.

> Use `evo-inquiry:result-to-claim` to assess which conclusions these raw
> results support and which alternative explanations remain.

Workflow checkpoint settings retain their original meaning: with
`AUTO_PROCEED=true`, authorized work continues in the same turn after reporting
the selected path. An explicitly blocking checkpoint still requires a reply.
Choose the mode that fits your project's supervision needs.

The beta installs the complete 83-entrypoint package. A proposed profile of
45 core and 38 optional entrypoints is documented in the
[inventory audit](SKILL_AUDIT_CN.md); it has not replaced the full installation.
Some entrypoints are workflow orchestrators, some are individual steps, and
some provide alternative backends. `paper-poster` is a retained deprecated
redirect; use `paper-poster-html` for new posters.

## Backends and beta limits

Plugin installation provides the skills and bundled helpers. Search services,
third-party reviewers, GPU platforms, image renderers, and LaTeX tooling need
their own dependencies and, where applicable, credentials. Configure only the
backends you intend to use. See [Codex backend compatibility](compatibility/codex-backends.md)
before using the retained generic/MiniMax review examples or image2 backend.

The inherited workflows mainly target ML/AI and related engineering research.
The principles are portable; broad discipline coverage is untested. Claude
Code and other retained client packages preserve upstream behavior and do not
apply the EvoInquiry layer in this beta.

Development validation included **777 passing tests and 20 skips**, successful
fresh-session discovery of all 83 entrypoints, and relocation to a directory
with spaces. See [the precise validation scope](docs/BETA_VALIDATION.md).
Live third-party providers, full research pipelines, and all operating systems
have not been verified end to end. A review score is not proof of a research
claim.

## Contribute and maintain

See [CONTRIBUTING.md](CONTRIBUTING.md). For local checks:

```sh
python -m pip install -r requirements-dev.txt
python tools/verify_evo_inquiry.py
python tools/check_skills_inventory.py
python -m pytest tests/ -q
```

Use tagged EvoInquiry updates. The retained upstream ARIS installers/updaters
target ARIS and can discard this customization when used as an EvoInquiry
update mechanism. New upstream snapshots should be integrated in a separate
branch, with the principles layer and compatibility checks reapplied.

## Origin and license

Derived from ARIS snapshot `3b19a22dc5a64c983d2eafd6c2c94000fadc4f8d`
by wanshuiyin. EvoInquiry customization is by lyd. The original skill bodies,
MIT license, and attribution are retained; see [NOTICE](NOTICE) and [LICENSE](LICENSE).
The original project documentation is preserved in
[README_ARIS.md](README_ARIS.md) and [README_CN_ARIS.md](README_CN_ARIS.md).
