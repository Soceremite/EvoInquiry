<!-- EI-WORKFLOW-REFERENCE -->

# Sub-skills used by this skill

Read this file when the workflow reaches Sub-skills used by this skill through Output Protocols. In commands and examples, interpret relative skill paths from the entrypoint directory.

### Sub-skills used by this skill

| Sub-skill | Phase | Purpose |
|-----------|:-----:|---------|
| `/research-lit` | 1 | Literature survey (if not already done) |
| `/novelty-check` | 1 | Verify the gap is real |
| `/research-review` | 2, 4 | Structural review + full draft review |
| `/paper-illustration` | 3 | Generate proposal figures (optional) |

### Funding Track (this skill's primary use case)

```
/idea-discovery "direction"              ← Workflow 1: find validated ideas
/research-refine "idea"                  ← sharpen the method
/grant-proposal "idea — KAKENHI"         ← this skill: write the grant proposal
                                          ← [submit & get funded]
/experiment-bridge                       ← implement experiments with funding
/auto-review-loop "results"              ← Workflow 2: iterate until submission-ready
/paper-writing                           ← Workflow 3: write the paper
```

### Publish Track (skip this skill)

```
/idea-discovery → /experiment-bridge → /auto-review-loop → /paper-writing → submit
```

## Output Protocols

> Follow these shared protocols for all output files:
> - **[Output Versioning Protocol](../../shared-references/output-versioning.md)** — write timestamped file first, then copy to fixed name
> - **[Output Manifest Protocol](../../shared-references/output-manifest.md)** — log every output to MANIFEST.md
> - **[Output Language Protocol](../../shared-references/output-language.md)** — respect the project's language setting
