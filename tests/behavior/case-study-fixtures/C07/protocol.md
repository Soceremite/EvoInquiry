# Synthetic generated-output evaluation

The eight PNGs are actual local fixture outputs drawn deterministically for
four predeclared prompts. They are toy artifacts, not outputs of a real trained
generator. All outputs use the same 72x72 canvas without crops. Baseline run b1,
candidate run c1, one draw per prompt, seed label 17. Matching integer labels do
not prove matching noise across real generator implementations. Sampler/step
settings for real models are not applicable to this toy fixture.

The CSV records fixture-annotator judgments of exact prompt adherence, not
model-judge scores. The primary local diagnostic outcome is adherence over
these four prompts. No reference images exist. Annotations may be used when
image inspection is unavailable, but do not claim to have viewed the files.

The separate reported distributional FID in distribution_metrics.json describes
another 1,000-output evaluation pool. Its assets and computation are unavailable.
Those numbers can be reported as supplied, not recomputed from these four PNG
pairs, and cannot be assigned per image.
