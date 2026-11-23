<!-- EI-WORKFLOW-REFERENCE -->

# Core Design Philosophy

Read this file when the workflow reaches Core Design Philosophy through Step 0: Pre-flight Check. In commands and examples, interpret relative skill paths from the entrypoint directory.





# Paper Illustration: Multi-Stage Codex-Supervised Figure Generation

Generate publication-quality illustrations using a **multi-stage workflow** with **Codex as the STRICT supervisor/reviewer**.

## Core Design Philosophy

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    MULTI-STAGE ITERATIVE WORKFLOW                        │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   User Request                                                           │
│       │                                                                  │
│       ▼                                                                  │
│   ┌─────────────┐                                                        │
│   │   Codex    │ ◄─── Step 1: Parse request, create initial prompt     │
│   │  (Planner)  │                                                        │
│   └──────┬──────┘                                                        │
│          │                                                               │
│          ▼                                                               │
│   ┌─────────────┐                                                        │
│   │   Gemini    │ ◄─── Step 2: Optimize layout description               │
│   │ (gemini-3-pro)│      - Refine component positioning                    │
│   │  Layout     │      - Optimize spacing and grouping                   │
│   └──────┬──────┘                                                        │
│          │                                                               │
│          ▼                                                               │
│   ┌─────────────┐                                                        │
│   │   Gemini    │ ◄─── Step 3: CVPR/NeurIPS style verification          │
│   │ (gemini-3-pro)│      - Check color palette compliance                  │
│   │  Style      │      - Verify arrow and font standards                 │
│   └──────┬──────┘                                                        │
│          │                                                               │
│          ▼                                                               │
│   ┌─────────────┐                                                        │
│   │ Paperbanana │ ◄─── Step 4: Render final image                       │
│   │ (gemini-3-  │      - High-quality image generation                   │
│   │ pro-image)  │      - Internal codename: Nano Banana Pro              │
│   └──────┬──────┘                                                        │
│          │                                                               │
│          ▼                                                               │
│   ┌─────────────┐                                                        │
│   │   Codex    │ ◄─── Step 5: STRICT visual review + SCORE (1-10)      │
│   │  (Reviewer) │      - Verify EVERY arrow direction                    │
│   │   STRICT!   │      - Verify EVERY block content                      │
│   └──────┬──────┘      - Verify aesthetics & visual appeal               │
│          │                                                               │
│          ▼                                                               │
│   Score ≥ 9? ──YES──► Accept & Output                                    │
│          │                                                               │
│          NO                                                              │
│          │                                                               │
│          ▼                                                               │
│   Generate SPECIFIC improvement feedback ──► Loop back to Step 2        │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Constants

- **IMAGE_MODEL = `gemini-3-pro-image-preview`** — Paperbanana (Nano Banana Pro) for image rendering
- **REASONING_MODEL = `gemini-3-pro-preview`** — Gemini for layout optimization and style checking
- **MAX_ITERATIONS = 5** — Maximum refinement rounds
- **TARGET_SCORE = 9** — Minimum acceptable score (1-10) — RAISED FOR QUALITY
- **OUTPUT_DIR = `figures/ai_generated/`** — Output directory
- **API_KEY_ENV = `GEMINI_API_KEY`** — Environment variable

## CVPR/ICLR/NeurIPS Top-Tier Conference Style Guide

**What "CVPR Style" Actually Means:**

### Visual Standards
- **Clean white background** — No decorative patterns or gradients (unless subtle)
- **Sans-serif fonts** — Arial, Helvetica, or Computer Modern; minimum 14pt
- **Subtle color palette** — Not rainbow colors; use 3-5 coordinated colors
- **Print-friendly** — Must be readable in grayscale (many reviewers print papers)
- **Professional borders** — Thin (2-3px), solid colors, not flashy

### Layout Standards
- **Horizontal flow** — Left-to-right is the standard for pipelines
- **Clear grouping** — Use subtle background boxes to group related modules
- **Consistent sizing** — Similar components should have similar sizes
- **Balanced whitespace** — Not cramped, not sparse

### Arrow Standards (MOST CRITICAL)
- **Thick strokes** — 4-6px minimum (thin arrows disappear when printed)
- **Clear arrowheads** — Large, filled triangular heads
- **Dark colors** — Black or dark gray (#333333); avoid colored arrows
- **Labeled** — Every arrow should indicate what data flows through it
- **No crossings** — Reorganize layout to avoid arrow crossings
- **CORRECT DIRECTION** — Arrows must point to the RIGHT target!

### Visual Appeal (科研风格 - Professional Academic Style)

**目标：既不保守也不花哨，找到平衡点**

#### ✅ 应该有的视觉元素：
- **Subtle gradient fills** — 淡雅的渐变填充（同色系从浅到深），不是炫彩
- **Rounded corners** — 圆角矩形（6-10px radius），现代感但不夸张
- **Clear visual hierarchy** — 通过大小、颜色深浅区分层次
- **Consistent color coding** — 统一的配色方案（3-4种主色）
- **Internal structure** — 大模块内部显示子组件（如Encoder内部的layer结构）
- **Professional typography** — 清晰的标签，适当的字号层次

#### ✅ 配色建议（学术专业）：
- **Inputs**: 柔和的绿色系 (#10B981 / #34D399)
- **Encoders**: 专业的蓝色系 (#2563EB / #3B82F6)
- **Fusion**: 优雅的紫色系 (#7C3AED / #8B5CF6)
- **Outputs**: 温暖的橙色系 (#EA580C / #F97316)
- **Arrows**: 黑色或深灰 (#333333 / #1F2937)
- **Background**: 纯白 (#FFFFFF)，不要花纹

#### ❌ 要避免的过度装饰：
- ❌ Rainbow color schemes (彩虹配色)
- ❌ Heavy drop shadows (重阴影效果)
- ❌ 3D effects / perspective (3D透视)
- ❌ Excessive gradients (夸张的多色渐变)
- ❌ Clip art / cartoon icons (卡通图标)
- ❌ Decorative patterns in background (背景花纹)
- ❌ Glowing effects (发光效果)
- ❌ Too many small icons (过多小图标)

#### ✓ 理想的视觉效果：
- 一眼看上去**专业、清晰**
- 有**适度的视觉吸引力**，但不抢眼
- 符合**CVPR/NeurIPS论文**的审美标准
- **打印友好**（灰度模式下也能清晰辨认）
- 像**精心设计**的学术图表，而不是PPT模板

### What to AVOID (CRITICAL)
- ❌ Rainbow color schemes (too many colors)
- ❌ Thin, hairline arrows (arrows must be THICK)
- ❌ Unlabeled connections
- ❌ Plain boring rectangles (add some visual interest)
- ❌ **Over-decorated with shadows/glows/icons** (too flashy)
- ❌ Small text that's unreadable when printed
- ❌ **WRONG arrow directions** — This is UNACCEPTABLE!

## Scope

| Figure Type | Quality | Examples |
|-------------|---------|----------|
| **Architecture diagrams** | Excellent | Model architecture, pipeline, encoder-decoder |
| **Method illustrations** | Excellent | Conceptual diagrams, algorithm flowcharts |
| **Conceptual figures** | Good | Comparison diagrams, taxonomy trees |

**Not for:** Statistical plots (use `/paper-figure`), photo-realistic images

## Workflow: MUST EXECUTE ALL STEPS

### Step 0: Pre-flight Check

```bash
# Check API key
if [ -z "$GEMINI_API_KEY" ]; then
    echo "ERROR: GEMINI_API_KEY not set"
    echo "Get your key from: https://aistudio.google.com/app/apikey"
    echo "Set it: export GEMINI_API_KEY='your-key'"
    exit 1
fi

# Create output directory
mkdir -p figures/ai_generated
```

