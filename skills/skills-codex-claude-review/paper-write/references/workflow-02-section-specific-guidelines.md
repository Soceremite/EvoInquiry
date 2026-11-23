<!-- EI-WORKFLOW-REFERENCE -->

# Section-Specific Guidelines

Read this file when the workflow reaches Section-Specific Guidelines through Step 5: Scientific Writing Quality Pass (5 audit passes). In commands and examples, interpret relative skill paths from the entrypoint directory.

#### Section-Specific Guidelines

**§0 Abstract:**
- Use the 5-part flow from `../shared-references/writing-principles.md`: what, why hard, how, evidence, strongest result
- Must be self-contained (understandable without reading the paper)
- Structure: problem → approach → key result → implication
- Include one concrete quantitative result
- 150-250 words (check venue limit)
- No citations, no undefined acronyms
- No `\begin{abstract}` — that's in main.tex

**§1 Introduction:**
- Open with a compelling hook (1-2 sentences, problem motivation)
- State the gap clearly ("However, ...")
- List contributions as a numbered or bulleted list
- End with a brief roadmap ("The rest of this paper is organized as...")
- Include the main result figure if space allows
- Target: 1.5 pages

**§2 Related Work:**
- **MINIMUM 1 full page** (3-4 substantive paragraphs). Short related work sections are a common reviewer complaint.
- Organize by category using `\paragraph{Category Name.}`
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

Trigger it when `PAPER_PLAN.md` labels the paper as theory/analysis, or when the drafted sections contain five or more formal result environments (`theorem`, `lemma`, `proposition`, or `corollary`).

**Proof source search:** search the workspace for standalone full-proof sources whose names or contents indicate a canonical proof version (`proof`, `appendix`, `full`, `complete`, `supplement`, `supplementary`). If one exists, ask:

`Inline full proofs from {file}? [Y/n]`

Default to `Y`. If accepted:

- import the full theorem/lemma statement plus proof block into the appendix source;
- use the main-body theorem statement as the canonical public statement;
- do not leave placeholders such as "see supplementary proof document" or "proof omitted for brevity";
- preserve theorem labels, equation labels, and proof structure exactly;
- keep main-body proof sketches short, but never let the appendix be sketch-only when a full proof source exists.

**Restatement audit:** compare every theorem/lemma/proposition statement restated in the appendix against the main-body version. Audit statements, hypotheses, case splits, quantifiers, domains, notation, variable names, and terminology for defined objects. Resolve all mismatches before Step 4.

### Step 4: Build Bibliography

**CRITICAL: Only include entries that are actually cited in the paper.**

1. Scan all `\citep{}` and `\citet{}` references in the drafted sections
2. Build a citation key list
3. For each citation key:
   - Check existing `.bib` files in the project/narrative docs
   - If not found and **DBLP_BIBTEX = true**, use the verified fetch chain below
   - If not found and **DBLP_BIBTEX = false**, search arXiv/Scholar for correct BibTeX
   - **NEVER fabricate BibTeX entries** — mark unknown ones with `[VERIFY]` comment
4. Write `references.bib` containing ONLY cited entries (no bloat)

#### Verified BibTeX Fetch (when DBLP_BIBTEX = true)

Three-step fallback chain — zero install, zero auth, all real BibTeX:

**Step A: DBLP (best quality — full venue, pages, editors)**
```bash
# 1. Search by title + first author
curl -s "https://dblp.org/search/publ/api?q=TITLE+AUTHOR&format=json&h=3"
# 2. Extract DBLP key from result (e.g., conf/nips/VaswaniSPUJGKP17)
# 3. Fetch real BibTeX
curl -s "https://dblp.org/rec/{key}.bib"
```

**Step B: CrossRef DOI (fallback — works for arXiv preprints)**
```bash
# If paper has a DOI or arXiv ID (arXiv DOI = 10.48550/arXiv.{id})
curl -sLH "Accept: application/x-bibtex" "https://doi.org/{doi}"
```

**Step C: Mark `[VERIFY]` (last resort)**
If both DBLP and CrossRef return nothing, mark the entry with `% [VERIFY]` comment. Do NOT fabricate.

**Why this matters:** LLM-generated BibTeX frequently hallucinates venue names, page numbers, or even co-authors. DBLP and CrossRef return publisher-verified metadata. Upstream skills (`/research-lit`, `/novelty-check`) may mention papers from LLM memory — this fetch chain is the gate that prevents hallucinated citations from entering the final `.bib`.

If the DBLP/CrossRef flow is not enough, load `../shared-references/citation-discipline.md` for stricter fallback rules before adding placeholders.

**Automated bib cleaning** — use this Python pattern to extract only cited entries:

```python
import re
# 1. Grep all \citep{...}, \citet{...}, and \cite{...} from all .tex files
# 2. Extract unique keys (handle multi-cite like \citep{a,b,c} or \cite{a,b,c})
# 3. Parse the full .bib file, keep only entries whose key is in the cited set
# 4. Write the filtered bib
```

This prevents bib bloat (e.g., 948 lines → 215 lines in testing).

**Citation verification rules (from claude-scholar + Imbad0202):**
1. Every BibTeX entry must have: author, title, year, venue/journal
2. Prefer published venue versions over arXiv preprints (if published)
3. Use consistent key format: `{firstauthor}{year}{keyword}` (e.g., `ho2020denoising`)
4. Double-check year and venue for every entry
5. Remove duplicate entries (same paper with different keys)

### Step 5: Scientific Writing Quality Pass (5 audit passes)

After drafting all sections, run five sequential audit passes. De-AI polish is included as one part of this quality pass, not a replacement for it.

**Pass 1: Clutter Extraction** — strip sentences to their cleanest components, remove filler, and remove AI-isms.

**Pass 2: Active Voice and Verb Vitality** — identify who did what, convert unnecessary passive voice, and resurrect smothered verbs.

**Pass 3: Sentence Architecture** — flag sentences over 40 words, keep subject and verb close, put familiar context first and new information later, and ensure each paragraph does one job.

**Pass 4: Keyword Consistency** — apply the Banana Rule: do not rename defined technical terms just to avoid repetition. If Methods defines a group, variable, or technique name, Results, Discussion, tables, and captions must use the same term.

**Pass 5: Numerical and Citation Integrity** — check sample sizes, percentages, significant figures, figure/table values, and whether citations support the claims they are attached to.

After drafting all sections, scan for common AI writing patterns and fix them:

First apply the sentence-level clarity rules from `../shared-references/writing-principles.md`:

- keep subject and verb close together
- put familiar context first and new information later
- place the most important information near the end of the sentence
- let each paragraph do one job
- use verbs for actions instead of nominalized nouns

**Content patterns to fix:**
- Significance inflation ("groundbreaking", "revolutionary" → use measured language)
- Formulaic transitions ("In this section, we..." → remove or vary)
- Generic conclusions ("This work opens exciting new avenues" → be specific)

**Language patterns to fix (watch words):**
- Replace: delve, pivotal, landscape, tapestry, underscore, noteworthy, intriguingly
- Remove filler: "It is worth noting that", "Importantly,", "Notably,"
- Avoid rule-of-three lists ("X, Y, and Z" appearing repeatedly)
- Don't start consecutive sentences with "This" or "We"

