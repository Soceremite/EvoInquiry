<!-- EI-WORKFLOW-REFERENCE -->

# Context

Read this file when the workflow reaches Context through Rationale. In commands and examples, interpret relative skill paths from the entrypoint directory.








# Auto Paper Improvement Loop: Review → Fix → Recompile

> 🔒 **Do not wrap this skill in `/loop`, `/schedule`, or `CronCreate`.** It
> already loops internally (review → fix → recompile) with its own round
> structure and a deliberate fresh-reviewer bias guard each round (no
> `codex-reply`). Re-asking it to "improve the paper" on a
> wall-clock timer produces no new signal — quality changes when the *review*
> changes, not when the clock ticks — and a timed re-run that also accepts its
> own output to decide when to stop crosses into self-acquittal
> (`acceptance-gate.md`). Schedule the *external wait that precedes it*, not the
> improvement loop. See
> [`shared-references/external-cadence.md`](../../shared-references/external-cadence.md).

Autonomously improve the paper at: **$ARGUMENTS**

## Context

This skill is designed to run **after** Workflow 3 (`/paper-plan` → `/paper-figure` → `/paper-write` → `/paper-compile`). It takes a compiled paper and iteratively improves it through external LLM review.

Unlike `/auto-review-loop` (which iterates on **research** — running experiments, collecting data, rewriting narrative), this skill iterates on **paper writing quality** — fixing theoretical inconsistencies, softening overclaims, adding missing content, and improving presentation.

## Constants

- **MAX_ROUNDS = 2** — Two rounds of review→fix→recompile. Empirically, Round 1 catches structural issues (4→6/10), Round 2 catches remaining presentation issues (6→7/10). Diminishing returns beyond 2 rounds for writing-only improvements.
- **REVIEWER_MODEL = `gpt-6-astra`** — Model used via Codex MCP for paper review.
- **REVIEWER_BIAS_GUARD = true** — When `true`, every review round uses a fresh `mcp__codex__codex` thread with no prior review context. Never use `mcp__codex__codex-reply` for review rounds. Set to `false` only for deliberate debugging of the legacy behavior. **Empirical evidence:** running the same paper with `codex-reply` + "since last round we did X" prompts inflated scores from real 3/10 → fake 8/10 across multiple rounds; switching to fresh threads recovered the true 3/10 assessment.
- **REVIEW_LOG = `PAPER_IMPROVEMENT_LOG.md`** — Cumulative log of all rounds, stored in paper directory.
- **HUMAN_CHECKPOINT = false** — When `true`, pause after each round's review and present score + weaknesses to the user. The user can approve fixes, provide custom modification instructions, skip specific fixes, or stop early. When `false` (default), runs fully autonomously.
- **EDIT_WHITELIST = `null`** — Optional path to a YAML/JSON whitelist file constraining which paths and operations the fix-implementation step may touch. When `null` (default), all edits proceed unconstrained. When set via `— edit-whitelist <path>` (also accepts `— edit_whitelist <path>`), the loop loads the file at startup and consults it before each edit; rejected edits are logged to `PAPER_IMPROVEMENT_LOG.md` rather than silently dropped. See "Optional: Edit Whitelist" below.

> 💡 Override: `/auto-paper-improvement-loop "paper/" — human checkpoint: true`

## Optional: Style reference (`— style-ref: <source>`, opt-in)

Lets the user steer **structural fixes only** during improvement (section reordering hints, paragraph length nudges, figure density adjustments) toward a reference paper. **Default OFF — when the user does not pass `— style-ref`, do nothing differently from before.**

Only when `— style-ref: <source>` appears in `$ARGUMENTS`, run the helper FIRST, before the loop starts:

```bash
# Resolve $STYLE_HELPER via the canonical strict-safe chain (see
# shared-references/integration-contract.md §2). Policy A — gate:
# unresolved helper means --style-ref cannot be satisfied, so abort.
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 1
if [ -z "${ARIS_REPO:-}" ] && [ -f .ei/installed-skills.txt ]; then
    ARIS_REPO=$(awk -F'\t' '$1=="repo_root"{print $2; exit}' .ei/installed-skills.txt 2>/dev/null) || true
fi
if [ -z "${ARIS_REPO:-}" ] && [ -f "$HOME/.ei/repo" ]; then
    ARIS_REPO=$(cat "$HOME/.ei/repo" 2>/dev/null) || true
fi
STYLE_HELPER=".ei/tools/extract_paper_style.py"
[ -f "$STYLE_HELPER" ] || STYLE_HELPER="tools/extract_paper_style.py"
[ -f "$STYLE_HELPER" ] || { [ -n "${ARIS_REPO:-}" ] && STYLE_HELPER="$ARIS_REPO/tools/extract_paper_style.py"; }
[ -f "$STYLE_HELPER" ] || {
  echo "ERROR: extract_paper_style.py not resolved at .ei/tools/, tools/, \$ARIS_REPO/tools/, or via ~/.ei/repo." >&2
  echo "       Fix: rerun bash tools/install_aris.sh or smart_update.sh (refreshes ~/.ei/repo), export ARIS_REPO, or copy the helper to tools/." >&2
  echo "       --style-ref cannot be satisfied; aborting." >&2
  exit 1
}
STYLE_STATUS=0
CACHE=$(python3 "$STYLE_HELPER" --source "<source>") || STYLE_STATUS=$?
case "$STYLE_STATUS" in
  0) ;;                                       # use $CACHE/style_profile.md as structural guidance for the FIX phase only
  2) echo "warning: style-ref skipped (missing optional dep)" >&2 ;;
  3) echo "error: --style-ref source failed; aborting loop" >&2 ; exit 1 ;;
  *) echo "error: helper failed unexpectedly; aborting loop" >&2 ; exit 1 ;;
esac
```

Sources accepted: local TeX dir / file, local PDF, arXiv id, http(s) URL. Overleaf URLs/IDs are rejected — clone via `/overleaf-sync setup <id>` first and pass the local clone path.

**Strict rules** (full contract in `tools/extract_paper_style.py` docstring):

- Use `style_profile.md` only during the **fix-implementation** phase, to nudge structural choices when applying reviewer feedback. Reviewer feedback always takes precedence; style ref is tie-breaker for *how* to apply a fix, not *whether* to apply it.
- **Never copy prose, claims, examples, or terminology** from anything reachable through the cache when implementing fixes.
- **Never pass `— style-ref` (or the cache contents) to the GPT-6-Astra reviewer sub-agent.** The Reviewer Independence Protocol below requires reviewers see only the artifact and the user's prompt — leaking the style ref would contaminate the review with author-side context. **This is the most critical invariant in this skill.**

## Optional: Edit Whitelist (`— edit-whitelist <path>`, opt-in)

Lets the caller hard-constrain which files and operations the **fix-implementation** step (Step 3 / Step 6) is allowed to touch. **Default OFF — when the user does not pass `— edit-whitelist` (or the alias `— edit_whitelist`), the loop applies all reviewer-driven edits without restriction, exactly as before.**

This is the parameter that upstream pipelines (e.g. `/resubmit-pipeline` Phase 2) use to enforce text-only resubmit microedits: no `.bib` mutations, no `.sty` / `.bst` mutations, no edits to prior-submission directories, no new `\cite{...}`, no new theorem environments, no new numerical claims.

### Schema

The whitelist file is YAML or JSON. All four sections are optional:

```yaml
allowed_paths:
  - sec/*.tex
  - main.tex
  - figures/*.tex
forbidden_paths:
  - "**/*.bib"
  - "**/*.sty"
  - "**/*.bst"
  - "../OldSubmission/**"
forbidden_operations:
  - new_cite              # blocks \cite{...}, \citep{...}, \citet{...}, \citeauthor{...} additions
  - new_bibitem           # blocks \bibitem{...} additions
  - new_theorem_env       # blocks \begin{theorem|lemma|proposition|corollary} additions
  - numerical_claim       # blocks adding new numbers / percentages / metrics
forbidden_deletions:      # operations that block REMOVALS, not additions
  - delete_existing_cite  # blocks removal of \cite{...} from the body (use citation-audit --soft-only instead)
  - delete_theorem_env    # blocks removal of an existing \begin{theorem|...} block
requires_user_approval_for:  # operations that don't auto-reject but pause for explicit user OK
  - rewrite_abstract      # paraphrasing the entire abstract triggers a checkpoint
  - rewrite_intro_first_para
  - delete_section
max_edits_per_round: 30   # hard cap on number of accepted edits per round (rejections are not counted; if cap is hit, remaining proposed edits are deferred to the next round with a warning)
rationale: "Resubmit mode: text-only microedits, paper structure frozen by user constraint."
```

### Resolution rules

- **`allowed_paths` empty AND `forbidden_paths` empty** → whitelist is a no-op (advisory: the file is loaded and `rationale` echoed to the log, but no path filtering is applied).
- **`allowed_paths` empty, `forbidden_paths` non-empty** → all paths NOT matched by `forbidden_paths` are mutable.
- **`allowed_paths` non-empty, `forbidden_paths` empty** → only paths matching `allowed_paths` are mutable.
- **Both non-empty** → an edit is allowed iff the target matches `allowed_paths` AND does NOT match `forbidden_paths`. `forbidden_paths` always wins on overlap.
- **`forbidden_operations` missing or empty** → no operation-level guard; only path-level filtering applies.

### Glob semantics

Use bash `extglob` / Python `fnmatch.fnmatch` semantics. `**` matches any depth (zero or more directory segments). Patterns are matched against the path **relative to the paper directory** (e.g. `paper/sec/intro.tex` matches `sec/*.tex` when paper-directory is `paper/`).

### Forbidden-operation detectors

For each candidate edit's diff (the new lines being added — deletions are exempt), the loop runs these regex checks and rejects if any forbidden operation matches:

| Operation | Detector (added lines only) |
|-----------|------------------------------|
| `new_cite` | `\\cite[a-zA-Z]*\{[^}]+\}` (catches `\cite`, `\citep`, `\citet`, `\citeauthor`, `\citeyear`, `\citealp`, etc.) |
| `new_bibitem` | `\\bibitem\{[^}]+\}` |
| `new_theorem_env` | `\\begin\{(theorem|lemma|proposition|corollary)\*?\}` |
| `numerical_claim` | New token matching `\b\d+(\.\d+)?%?\b` that did NOT appear in the deleted/replaced lines (i.e. genuinely new numbers, not edits to existing ones) |

### Behavior at loop start (before Round 1 fix-implementation)

1. If `— edit-whitelist <path>` is present in `$ARGUMENTS`, set `EDIT_WHITELIST = <path>`.
2. Load the file (`yaml.safe_load`; if it fails, fall back to `json.loads`). On load failure, abort the loop with a clear error — do NOT silently proceed unconstrained.
3. Echo `rationale` (if present) into `PAPER_IMPROVEMENT_LOG.md` under a new "Edit Whitelist" preamble section so the audit trail records why edits were constrained.

### Behavior during fix-implementation (Steps 3 and 6)

Before applying each proposed edit:

1. Resolve target file path relative to the paper directory.
2. Path check: if `allowed_paths` is non-empty, target must match at least one pattern. Then if `forbidden_paths` is non-empty, target must NOT match any pattern. If either fails → reject as `path` violation.
3. Operation check: build the unified diff (or just the set of newly-added lines) for the proposed edit. For each entry in `forbidden_operations`, run its detector on the added lines. If any detector matches → reject as `operation` violation.
4. If all checks pass, apply the edit normally.
5. If rejected, append an entry to `PAPER_IMPROVEMENT_LOG.md` under a `## Rejected by edit_whitelist (Round N)` heading with this schema:
   ```
   - file: <relative path>
     reason: path | operation
     pattern: <the offending forbidden_path glob, OR the offending forbidden_operation name + the matched substring>
     reviewer_concern: <the original Round-N weakness that motivated this edit>
   ```
6. Continue with the remaining edits in the round. Do NOT abort the whole round on a single rejection.

### End-of-round surfacing

At the end of each round (after the recompile, before moving to the next round), if any edits were rejected during that round's fix step:

- Print a one-line summary to the round's checkpoint output: `Edit whitelist rejected N edits this round (M path, K operation). See PAPER_IMPROVEMENT_LOG.md "Rejected by edit_whitelist (Round N)".`
- If `HUMAN_CHECKPOINT = true`, include the rejection list in the checkpoint shown to the user before they approve next-round fixes.

### Example invocations

```bash
# Resubmit-pipeline Phase 2 caller (text-only mode):
/auto-paper-improvement-loop "paper/" — edit-whitelist .resubmit/edit_whitelist.yaml

# Aliased form is accepted:
/auto-paper-improvement-loop "paper/" — edit_whitelist .resubmit/edit_whitelist.yaml

# Combined with other flags:
/auto-paper-improvement-loop "paper/" — human checkpoint: true — edit-whitelist constraints.yaml
```

### Rationale

Without a whitelist, the loop's reviewer-driven fix step is free to add citations, introduce new theorem environments, or tweak numerical claims — all of which are reasonable for first-submission polish but **forbidden** in resubmit / camera-ready / rebuttal-only modes where the paper structure is frozen by external constraint. Routing those constraints through a first-class parameter (rather than relying on the LLM to "remember" not to do them) makes the constraint enforceable, auditable via `PAPER_IMPROVEMENT_LOG.md`, and visible to the user at each round's checkpoint.

