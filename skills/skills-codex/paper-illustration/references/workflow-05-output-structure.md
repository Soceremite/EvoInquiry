<!-- EI-WORKFLOW-REFERENCE -->

# Output Structure

Read this file when the workflow reaches Output Structure through Model Summary. In commands and examples, interpret relative skill paths from the entrypoint directory.

## Output Structure

```
figures/ai_generated/
├── layout_description.txt  # Step 2: Gemini layout optimization output
├── style_spec.txt          # Step 3: Gemini style verification output
├── figure_v1.png           # Iteration 1 (Paperbanana render)
├── figure_v2.png           # Iteration 2
├── figure_v3.png           # Iteration 3
├── figure_final.png        # Accepted version (copy of best, score ≥ 9)
├── latex_include.tex       # LaTeX snippet
└── review_log.json         # All review scores and STRICT feedback
```

## Model Summary

| Stage | Model | Purpose |
|-------|-------|---------|
| Step 1 | Codex | Parse request, create initial prompt |
| Step 2 | gemini-3-pro | Layout optimization (positioning, spacing, grouping) |
| Step 3 | gemini-3-pro | CVPR/NeurIPS style verification |
| Step 4 | gemini-3-pro-image-preview (Paperbanana) | High-quality image rendering |
| Step 5 | Codex | STRICT visual review and scoring |
