# Code reuse and interface documentation

Apply this contract inside implementation and modification work. Do not add a
separate documentation-audit skill to every request.

Before changing research code, inspect the relevant code map or small module
guide, then the actual interface, implementation, callers and tests. Reuse a
compatible fixed implementation. Extend with a small tested hook when needed.
Promote code to research_shared after a real second consumer and stable boundary
exist; a project need not share one trainer, tokenizer or augmentation pipeline.

A shared data interface fixes sample identity, split, label map and batch
protocol. Method-specific tokenization, augmentation and sampling stay explicit
variant configuration. Shared preprocessing must not erase a scientific
difference or mix train-fitted statistics into validation/test fitting.

Give new or changed public interfaces and core scientific routines concise
docstrings beside the code: purpose; each parameter's meaning, relevant defaults
and constraints; returned values and their meaning. For array/tensor inputs and
outputs, name shape, axis order and dtype; explain masks, labels, units and empty
or missing-data behavior where relevant. State consequential exceptions,
mutation/I/O/RNG and split/statistics assumptions. Document CLI argument formats
and distinguish a file path from an inline object. Add a minimal call when usage
is ambiguous. Use inline comments for non-obvious transformations or choices,
including a fixed primary source where relevant; avoid narrating obvious lines
or padding trivial private helpers. Update comments when behavior changes.

Before running the first consumer or handing off changed scientific code, check
the new or changed routines themselves: does each local interface description
match its actual parameters, shapes and returned values? A module summary or
fresh code map does not perform this check. Correct missing or stale contracts
beside the routine, without expanding the change to untouched helpers.

Change code, docstrings/examples, callers and tests together. Exercise a
representative caller for changed semantics; run contract tests and consumer
regressions for shared changes. An evaluator fix gets a new version; retain
affected old results, identify their scope and rerun the necessary baselines
before comparing new results.

tools/code_map.py build_map/check_freshness/resolve_symbol index qualified symbols,
paths, purpose, examples, callers/tests and source/doc hashes. Use build/check/
resolve CLI commands. JSON is valid YAML for docs/code-map.yaml. Do not copy full
function bodies or rely on drifting line numbers. Annotate dynamic entrypoints.
Implementation changes make navigation stale; a body change with unchanged
public docs calls for a documentation review. A fresh map cannot certify
semantic correctness or detect every missing explanation.

[PEP 257](https://peps.python.org/pep-0257/) gives docstring conventions.
Executable contract tests, not comments alone, check shape, label ranges,
split separation and unchanged evaluation statistics.
