<!-- EI-WORKFLOW-REFERENCE -->

# Step 2: Generate math_commands.tex

Read this file when the workflow reaches Step 2: Generate math_commands.tex through Step 4: Build Bibliography. In commands and examples, interpret relative skill paths from the entrypoint directory.

### Step 2: Generate math_commands.tex

Create shared math macros based on the paper's notation:

```latex
% math_commands.tex — shared notation
\newcommand{\R}{\mathbb{R}}
\newcommand{\E}{\mathbb{E}}
\DeclareMathOperator*{\argmin}{arg\,min}
\DeclareMathOperator*{\argmax}{arg\,max}
% Add paper-specific notation here
```

### Step 3: Write Each Section

Process sections in order. For each section:

1. **Read the plan** — what claims, evidence, citations belong here
2. **Read NARRATIVE_REPORT.md** — extract relevant content, findings, and quantitative results
3. **Draft content** — write complete LaTeX (no fabricated placeholders). **Exception:** if `GAP_REPORT.md` exists and the section has slots with `status: missing`, emit `<!-- DATA_NEEDED: <Slot ID> — <description> -->` at those points instead of inventing data — see the DATA_NEEDED markers subsection above.
4. **Insert figures/tables** — use snippets from `figures/latex_includes.tex`
5. **Add citations** — for ML conferences (ICLR/NeurIPS/ICML/CVPR/ACL/AAAI): use `\citep{}` / `\citet{}` (natbib). **For IEEE venues**: use `\cite{}` (numeric style via `cite` package). Never mix natbib and cite commands.

Before drafting the front matter, re-read the one-sentence contribution from `PAPER_PLAN.md`. The Abstract and Introduction should make that takeaway obvious before the reader reaches the full method.

#### Section-Specific Guidelines

**§0 Abstract:**
- Use the 5-part flow from `../shared-references/writing-principles.md`: what, why hard, how, evidence, strongest result
- Must be self-contained (understandable without reading the paper)
- Start with the paper's specific contribution, not generic field-level background
- Include one concrete quantitative result
- 150-250 words (check venue limit)
- No citations, no undefined acronyms
- No `\begin{abstract}` — that's in main.tex

**§1 Introduction:**
- Open with a compelling hook (1-2 sentences, problem motivation)
- State the gap clearly ("However, ...")
- Give a brief approach overview before the reader gets lost in details
- List 2-4 specific, falsifiable contributions as a numbered or bulleted list
- Preview the strongest result early instead of saving it for the experiments section
- End with a brief roadmap ("The rest of this paper is organized as...")
- Include the main result figure if space allows
- Target: 1-1.5 pages
- Methods should begin by page 2-3 at the latest

**§2 Related Work:**
- **MINIMUM 1 full page** (3-4 substantive paragraphs). Short related work sections are a common reviewer complaint.
- Organize by category using `\paragraph{Category Name.}`
- Organize methodologically, by assumption class, or by research question; do not write paper-by-paper mini-summaries
- Each category: 1 paragraph summarizing the line of work + 1-2 sentences positioning this paper
- Do NOT just list papers — synthesize and compare
- End each paragraph with how this paper relates/differs

**§3 Method / Preliminaries / Setup:**
- Define notation early (reference math_commands.tex)
- Use `\begin{definition}`, `\begin{theorem}` environments for formal statements
- For theory papers: include proof sketches of key results in main body, full proofs in appendix
- For theory papers: include a **comparison table** of prior bounds vs. this paper
- Include algorithm pseudocode if applicable (`algorithm2e` or `algorithmic`)
- Target: 1.5-2 pages

**§4 Experiments:**
- Start with experimental setup (datasets, baselines, metrics, implementation details)
- Main results table/figure first
- Then ablations and analysis
- Every claim from the introduction must have supporting evidence here
- For each major experiment, make explicit what claim it supports and what the reader should notice
- Target: 2.5-3 pages

**§5 Conclusion:**
- Summarize contributions (NOT copy-paste from intro — rephrase)
- Limitations (2-4 material, specific limits — dataset scale, compute regime, assumption X; real ones only, never invented to fill a count. This section is the ONLY home for generic caveats)
- Future work (1-2 concrete directions)
- Ethics statement and reproducibility statement (if venue requires)
- Target: 0.5 pages

**Appendix:**
- Proof details (full proofs of main-body theorems)
- Additional experiments, ablations
- Implementation details, hyperparameter tables
- Additional visualizations

### Step 3.5: Theory Paper Consistency Pass (theory papers only)

Run this pass after drafting all sections and before building the bibliography.

**Trigger heuristic:** treat the paper as theory-heavy if `PAPER_PLAN.md` labels it as theory/analysis, or if the drafted sections contain 5 or more formal result environments (`\begin{theorem}`, `\begin{lemma}`, `\begin{proposition}`, `\begin{corollary}`).

**Proof source search:** search the workspace for any standalone full-proof source file whose name or contents indicate a canonical proof version (`proof`, `appendix`, `full`, `complete`, `supplement`, `supplementary`). If such a file exists, prompt the user exactly:

`Inline full proofs from {file}? [Y/n]`

Default to `Y`.

If the user accepts:
- import the full theorem/lemma statement plus proof block into the appendix source (`A_appendix.tex` or the appendix file named by the plan)
- use the main-body theorem statement as the canonical public statement; the appendix copy must match it unless the main-body statement is being revised in the same pass
- do **not** leave placeholders such as "see supplementary proof document" or "proof omitted for brevity"
- preserve theorem labels, equation labels, and proof structure exactly
- keep the main body proof sketches short, but never let the appendix be a sketch-only placeholder when a full proof source exists

If no standalone full-proof source exists:
- use proof sketches only when they are actually written as proof sketches, not placeholders
- do not fabricate an external proof document reference

**Restatement audit:**
- Compare every theorem/lemma/proposition statement that is restated in the appendix against the main-body version
- Do not diff proof bodies; only audit statements, hypotheses, case splits, quantifiers, domains, notation, variable names, and terminology for defined objects
- Treat `stationary` vs `terminal`, changed assumption names, or missing case splits as mismatches unless explicitly documented
- If the appendix needs different wording, add an explicit notation bridge instead of silently renaming concepts
- Resolve all mismatches before Step 4

**Empirical motivation:** in a real theory-paper run, the default behavior generated `"see supplementary proof document"` placeholders in the appendix. The author had to manually pull hundreds of lines of full proofs from a standalone proofs file (e.g. `proof_full.tex`). Without this pass, theory papers ship with sketch-only appendices that fail at theory venues.

### Step 4: Build Bibliography

**CRITICAL: Only include entries that are actually cited in the paper.**

1. Scan all citation references in the drafted sections (`\citep{}`/`\citet{}` for ML conferences, `\cite{}` for IEEE venues)
2. Build a citation key list
3. For each citation key:
   - Check existing `.bib` files in the project/narrative docs
   - If not found and **DBLP_BIBTEX = true**, use the verified fetch chain below
   - If not found and **DBLP_BIBTEX = false**, search arXiv/Scholar for correct BibTeX
   - **NEVER fabricate BibTeX entries** — mark unknown ones with `[VERIFY]` comment
4. Write `references.bib` containing ONLY cited entries (no bloat)

