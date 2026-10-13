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

Document public interfaces with purpose/boundaries and a minimal call; input and
output types, shape/axis order, dtype, label meaning, units/ranges/missing values;
preconditions and split/statistics sources; exceptions, I/O/cache/state/RNG and
concurrency effects; caller invariants, tests and compatibility migration.
Explain non-obvious algorithm choices with a fixed primary source when relevant.
Keep ordinary private helpers concise.

Change code, docstrings/examples, callers and tests together. Run contract tests
and representative consumer regressions for shared changes. An evaluator fix
gets a new version; retain affected old results, identify their scope and rerun
the necessary baselines before comparing new results.

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
