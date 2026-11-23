<!-- EI-WORKFLOW-REFERENCE -->

# Step 5: Codex STRICT Visual Review & Scoring (MANDATORY)

Read this file when the workflow reaches Step 5: Codex STRICT Visual Review & Scoring (MANDATORY) through Key Rules (MUST FOLLOW - STRICT). In commands and examples, interpret relative skill paths from the entrypoint directory.

### Step 5: Codex STRICT Visual Review & Scoring (MANDATORY)

**Codex MUST read the generated image and perform a STRICT review:**

1. **Visual Analysis**: What does the image show in detail?
2. **Strengths**: What's good about it?
3. **STRICT Verification**: Check EVERY item below
4. **Score**: Rate 1-10 (10 = perfect) — BE STRICT!

**STRICT Review Template:**

```markdown
## Codex's STRICT Review of Figure v{N}

### What I See
[Describe the generated image in DETAIL - every block, every arrow]

### Strengths
- [Strength 1]
- [Strength 2]

### ═══════════════════════════════════════════════════════════════
### STRICT VERIFICATION CHECKLIST (ALL must pass for score ≥ 9)
### ═══════════════════════════════════════════════════════════════

#### A. Arrow Correctness Verification (CRITICAL - any failure = score ≤ 6)
Check EACH arrow:
- [ ] Arrow 1: [Source] → [Target] — Does it point to the CORRECT target?
- [ ] Arrow 2: [Source] → [Target] — Does it point to the CORRECT target?
- [ ] Arrow 3: [Source] → [Target] — Does it point to the CORRECT target?
- [ ] Arrow 4: [Source] → [Target] — Does it point to the CORRECT target?
- [ ] Arrow 5: [Source] → [Target] — Does it point to the CORRECT target?
- [ ] Arrow 6: [Source] → [Target] — Does it point to the CORRECT target?

#### B. Block Content Verification (any failure = score ≤ 7)
Check EACH block:
- [ ] Block 1 "[Name]": Has correct label? Has sub-label? Content correct?
- [ ] Block 2 "[Name]": Has correct label? Has sub-label? Content correct?
- [ ] Block 3 "[Name]": Has correct label? Has sub-label? Content correct?
- [ ] Block 4 "[Name]": Has correct label? Has sub-label? Content correct?
- [ ] Block 5 "[Name]": Has correct label? Has sub-label? Content correct?
- [ ] Block 6 "[Name]": Has correct label? Has sub-label? Content correct?
- [ ] Block 7 "[Name]": Has correct label? Has sub-label? Content correct?

#### C. Arrow Visibility (any failure = score ≤ 7)
- [ ] ALL arrows are THICK (≥5px visible stroke)
- [ ] ALL arrows have CLEAR arrowheads (large triangular heads)
- [ ] ALL arrows are BLACK or DARK GRAY (not light colors)
- [ ] NO arrows are too thin or invisible

#### D. Arrow Labels (any failure = score ≤ 7)
- [ ] EVERY arrow has a text label
- [ ] Labels are readable (not too small)
- [ ] Labels correctly describe the data flowing

#### E. Visual Appeal (科研风格 - Balanced Academic Style) (any failure = score ≤ 8)
- [ ] **有适度视觉吸引力** — 有subtle渐变或圆角，但不夸张
- [ ] **不是平淡方块** — 有一定设计感
- [ ] **不过度装饰** — 没有重阴影、发光效果、彩虹配色
- [ ] **专业学术风格** — 像CVPR论文中的图表，不是PPT模板
- [ ] **Internal structure visible** — 大模块内部显示子组件结构
- [ ] **Color palette: 3-4种协调色** — 不是彩虹，也不是纯黑白

#### E2. Visual Appeal - RED FLAGS (immediate score ≤ 7 if found)
- [ ] **NO heavy drop shadows** (重阴影 = too flashy)
- [ ] **NO glowing effects** (发光效果 = too flashy)
- [ ] **NO rainbow gradients** (彩虹渐变 = unprofessional)
- [ ] **NO excessive decorative icons** (过多装饰图标 = distracting)

#### F. Layout & Flow (any failure = score ≤ 7)
- [ ] Clean horizontal left-to-right flow
- [ ] No arrow crossings
- [ ] Data flow traceable in 5 seconds
- [ ] Balanced spacing (not cramped, not sparse)

#### G. Style Compliance
- [ ] CVPR/NeurIPS professional style
- [ ] Color palette appropriate (not rainbow)
- [ ] Font readable
- [ ] Print-friendly (grayscale test)

### ═══════════════════════════════════════════════════════════════

### Issues Found (BE SPECIFIC)
1. [Issue 1]: [EXACTLY what is wrong] → [How to fix]
2. [Issue 2]: [EXACTLY what is wrong] → [How to fix]
3. [Issue 3]: [EXACTLY what is wrong] → [How to fix]

### Score: X/10

### STRICT Score Breakdown Guide:
- **10**: Perfect. No issues. Publication-ready masterpiece. 视觉风格完美平衡。
- **9**: Excellent. Minor issues that don't affect understanding. 可以直接使用。
- **8**: Good but has noticeable issues. 视觉上太平淡或太花哨都需要改进。
- **7**: Usable but has clear problems. 箭头或内容有问题。
- **6**: Has arrow direction errors (箭头指向错误) OR missing major components.
- **1-5**: Major issues. Unacceptable.

### Visual Style Scoring (视觉风格评分):
- **太花哨 (Too flashy)**: 重阴影、发光效果、彩虹配色 → score ≤ 7
- **太平淡 (Too plain)**: 纯黑白方块、无任何视觉设计 → score ≤ 8
- **恰到好处 (Balanced)**: 适度渐变、圆角、清晰层次 → score 9-10

### Verdict
[ ] ACCEPT (score ≥ 9 AND all critical checks pass)
[ ] REFINE (score < 9 OR any critical check fails)

**If REFINE: List the EXACT issues that must be fixed**
```

### Step 6: Decision Point

```
IF score >= 9 AND all critical checks pass:
    → Accept figure, generate LaTeX snippet, DONE
ELSE IF iteration < MAX_ITERATIONS:
    → Generate SPECIFIC improvement prompt based on EXACT issues
    → Go to Step 2 (Gemini Layout) with refined prompt
ELSE:
    → Max iterations reached, show best version
    → Ask user if they want to continue or accept
```

### Step 7: Generate Improvement Prompt (for refinement)

**Codex generates TARGETED improvement prompt with EXACT issues:**

```
Refine this academic diagram. This is iteration {N}.

## ═══════════════════════════════════════════════════════════════
## CRITICAL: Fix These EXACT Issues (from previous review)
## ═══════════════════════════════════════════════════════════════

### Arrow Direction Errors (MUST FIX):
1. [EXACT issue]: Arrow from [A] to [B] is pointing to wrong target. It should point to [C] instead.
2. [EXACT issue]: ...

### Missing Arrow Labels (MUST FIX):
1. Arrow from [A] to [B] is missing label "[data type]"
2. ...

### Block Content Issues (MUST FIX):
1. Block "[Name]" has wrong label. Should be "[correct label]"
2. ...

### Visual Appeal Issues (SHOULD FIX):
1. Blocks are too plain. Add [gradients/shadows/internal structure]
2. ...

## Keep These Good Elements:
- [What to preserve from previous version]

## Generate the improved figure with ALL issues fixed.
```

### Step 8: Final Output

When figure is accepted (score ≥ 9):

```latex
% === AI-Generated Figure ===
\begin{figure*}[t]
    \centering
    \includegraphics[width=0.95\textwidth]{figures/ai_generated/figure_final.png}
    \caption{[Caption based on user's original request].}
    \label{fig:[label]}
\end{figure*}
```

## Key Rules (MUST FOLLOW - STRICT)

1. **NEVER skip the review step** — Always read and STRICTLY score the image
2. **NEVER accept score < 9** — Keep refining until excellence
3. **VERIFY EVERY ARROW DIRECTION** — Wrong direction = automatic fail (score ≤ 6)
4. **VERIFY EVERY BLOCK CONTENT** — Wrong content = automatic fail (score ≤ 7)
5. **BE SPECIFIC in feedback** — "Arrow from A to B points to wrong target C" not "arrow is wrong"
6. **SAVE all iterations** — Keep version history for comparison
7. **Codex is the STRICT boss** — Accept only excellence, not "good enough"
8. **ARROW CORRECTNESS IS NON-NEGOTIABLE** — Any wrong arrow direction = reject
9. **VISUAL APPEAL MATTERS** — Plain boring figures = score ≤ 8
10. **Target score is 9** — Not 8, not "good enough"
11. **USE MULTI-STAGE WORKFLOW** — Codex → Gemini Layout → Gemini Style → Paperbanana → Codex Review
12. **USE CORRECT MODELS** — gemini-3-pro for reasoning, gemini-3-pro-image-preview for rendering

