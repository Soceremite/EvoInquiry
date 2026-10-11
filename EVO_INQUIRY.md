# EvoInquiry

EvoInquiry is a Codex research-workflow edition of ARIS. It retains the upstream
research workflows and adds six portable principles: independent judgment,
grounded inquiry, explanatory simplicity, discriminating research, honest
conclusions, and reflective progress.

The principles are maintained once in
[the shared reference](skills/skills-codex/shared-references/evo-inquiry.md).
All 83 Codex skill entrypoints carry a short reference. Each skill applies only
the parts relevant to its task. There are no universal training budgets,
mandatory GPU/CPU gates, fixed review cadences, or project-specific paths.
Project instructions and existing authorization still govern the actual work.

## Origin and compatibility

Based on the installed ARIS snapshot at commit
`3b19a22dc5a64c983d2eafd6c2c94000fadc4f8d`, from
https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep.
The upstream MIT license and author attribution are retained in LICENSE and
NOTICE. The EvoInquiry customization is by lyd.

This first edition customizes the Codex package only. The Claude Code package
and other reviewer overlays are retained as upstream implementations and do
not claim to apply the EvoInquiry principles. Existing child skill names, parameters,
artifacts, .aris state paths, helper interfaces, and review contracts remain.
The Codex plugin identity becomes `evo-inquiry`; its namespaced skills are
`evo-inquiry:<existing-skill-name>`. Changes are additive instruction blocks,
shared principles and targeted compatibility corrections, Codex presentation
metadata, and matching test updates. The inherited skill bodies are preserved.

## Install and rollback

Register this directory as a local marketplace, then install its plugin:

```sh
codex plugin marketplace add "$PWD"
codex plugin add evo-inquiry@evo-inquiry
```

The source remains separate from the installed cache. After validating the new
installation, enable `evo-inquiry@evo-inquiry` and disable `aris@aris` in the
active Codex user config. Start a new session to verify actual skill discovery.
Do not uninstall or rewrite the original ARIS package. To roll back, disable
the new plugin and re-enable `aris@aris`; preserve unrelated config settings.
Run these commands from the extracted package root. Register its actual
directory when moving the package. External backends require separate setup;
see [Codex backend compatibility](compatibility/codex-backends.md).

Public validation scope is documented in
[docs/BETA_VALIDATION.md](docs/BETA_VALIDATION.md). Tagged releases include
redistribution archives and their checksums. Static checks establish packaging
and compatibility, not guaranteed
scientific judgment in every future session. Behavioral checks are limited
synthetic exercises and are reported as such.

## Inventory review

See [SKILL_AUDIT_CN.md](SKILL_AUDIT_CN.md) for the 83-entrypoint inventory,
retired redirect, backend alternatives, Codex documentation issues, and optional
modules. The audit does not change the installed inventory or upstream workflows.

## Maintenance and validation scope

The retained upstream installers and updaters target ARIS. EvoInquiry updates
should start from a separate staging copy of the chosen upstream snapshot,
reapply this layer, and pass the preservation and regression checks before
replacing an active installation. Installing plain ARIS over this package can
discard the principles layer. An EvoInquiry-specific automatic updater is
not part of this edition.

This beta retains ML/AI-oriented workflows and portable research principles.
The public validation report records test results and limitations; raw local
session records are excluded from the public package. External service setup,
cross-platform operation, and broad discipline coverage require their own
evidence before a release advertises them as supported.

The supported EvoInquiry installation route in this edition is the local
Codex marketplace plugin described above. The retained standalone ARIS
installers and other client packages are upstream compatibility resources;
their presence does not establish support for installing this customization
through every ARIS installation mode.
