# Contributing to EvoInquiry

[中文](CONTRIBUTING_CN.md)

Report reproducible issues and proposed improvements through this repository's
Issues and pull requests. Include the affected skill, Codex version, expected
behavior, observed behavior, and the minimum shareable input. Remove credentials,
private research data, and unpublished invention details from examples.

Research principles live in `skills/skills-codex/shared-references/evo-inquiry.md`.
Keep them concise and portable across projects. Project-specific preferences
belong in the project's own instructions. Other client packages currently retain
the upstream implementations.

Preserve workflow output/recovery contracts and explicit authorization boundaries.
Inspect callers before removing or combining entrypoints. Default dependency
edges are maintained in `tools/skill-groups.tsv`; optional branches may add
dependencies beyond that catalog. Describe backend availability from observed
checks rather than from the existence of a skill file.

Run the checks in README.md, with focused behavior tests when the change needs
them. Distinguish simulated tests, local integration tests, live provider checks,
and research evidence. Document unresolved limits. Cross-platform CI results
should accompany installation changes.

Upstream ARIS documentation is retained in `README_ARIS.md`, `README_CN_ARIS.md`,
`CONTRIBUTING_ARIS.md`, and `CONTRIBUTING_CN_ARIS.md`. Preserve its license and
attribution when integrating a new snapshot. Contributions to EvoInquiry are
distributed under the MIT license.
