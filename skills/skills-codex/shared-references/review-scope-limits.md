# Review scope and evidence

Use the actual research question, artifacts, user scope and applicable standards.
The reviewer may find both strengths and material defects. A proposal to change
the work needs an observed problem, missing evidence or an existing invariant;
unrelated redesign is optional.

## The block

Carry this scope into reviewer prompts that can propose changes:

```text
=== REVIEW SCOPE ===
Evaluate the actual research question, requested deliverable and applicable
disciplinary standards. Locate strengths and defects in the supplied evidence;
do not presume acceptance, rejection or a particular threat model. Distinguish
observed errors, unsupported claims and optional extensions. Propose the smallest
adequate correction, citing its failing path, evidence or preserved invariant.
Keep hypotheses, speculation and unperformed checks explicit. A real boundary
or reproducibility defect is in scope when it affects this work; unrelated
infrastructure and speculative redesign are not automatically required.
Say plainly when something is correct. Do not manufacture findings.
```

## Apply proportionately

Report real measurement, implementation, reproducibility and trust-boundary
problems when they affect the work. Do not assume a toolkit-specific threat
model or prohibit a class of correction regardless of the research question.
Distinguish a demonstrated defect from a hypothetical concern. Verify factual
premises and cite the affected evidence.

Attach each limitation to the conclusion it actually limits. Missing raw
artifacts prevent independent execution verification; an unavailable required
review prevents that review's completion. Preserve narrower conclusions
supported by supplied records without certifying unperformed checks or turning
an unknown into a demonstrated failure.

A single requested review can finish with unresolved issues and a bounded
next step. Agreement, publication scores and the absence of newly found defects
are not proof that a research claim is true. Specialized adversarial reviews
retain their role, with a separate evidence-grounded final judgment.

## Related

- [acceptance-gate](acceptance-gate.md)
- [reviewer-independence](reviewer-independence.md)
- [reviewer-routing](reviewer-routing.md)
