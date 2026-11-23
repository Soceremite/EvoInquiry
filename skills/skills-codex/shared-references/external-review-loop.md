# External research review loop

Read the [shared review cycle](research-review-cycle.md) for issue closure,
state recovery, and stopping. The selected adapter owns the loop. Use the
default four rounds or the existing explicit cap. Record each round before
continuation and retain the run ID, attempts, pending experiments, original
budget and output paths. Reuse the existing owner on resume.

Send the reviewer the original question, relevant evidence, changes and
unresolved concerns. Ask for a score out of ten, a `ready | almost | not ready`
verdict, evidence-backed strengths, material weaknesses and minimum useful
fixes. Preserve the raw response, actual API/model provenance and failure
receipt. Apply the existing [reviewer independence](reviewer-independence.md)
and evidence-closure rules before claiming acceptance.

Keep credentials out of prompts, logs and source snapshots. If the selected
backend is unavailable, preserve pending state and record the specific BLOCKED
condition. Obtain authorization before changing backend or configuration.
Age alone does not create a new budget or reset an existing run.

Store `review-stage/AUTO_REVIEW.md` and `review-stage/REVIEW_STATE.json`, or use
the existing legacy paths on resume. Follow the shared
[versioning](output-versioning.md), [manifest](output-manifest.md), and
[language](output-language.md) protocols.
