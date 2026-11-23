<!-- EI-WORKFLOW-REFERENCE -->

# Scope

Read this file when the workflow reaches Scope through Step 2: Gemini Layout Optimization (gemini-3-pro). In commands and examples, interpret relative skill paths from the entrypoint directory.

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

### Step 1: Claude Plans the Figure (YOU ARE HERE)

**CRITICAL: Claude must first analyze the user's request and create a detailed prompt.**

Parse the input: **$ARGUMENTS**

Claude's task:
1. Understand what figure the user wants
2. Identify all components, connections, data flow
3. Create a **detailed, structured prompt** for Gemini
4. Include style requirements AND visual appeal requirements

**Prompt Template for Claude to generate:**

```
Create a PROFESSIONAL, VISUALLY APPEALING publication-quality academic diagram following CVPR/ICLR/NeurIPS standards.

## Visual Style: 科研风格 (Academic Professional Style)
### 目标：平衡 — 既不保守也不花哨

#### DO (应该有):
- **Subtle gradients** — 同色系淡雅渐变（如 #2563EB → #3B82F6），不是多色炫彩
- **Rounded corners** — 圆角矩形（6-10px），现代感
- **Clear visual hierarchy** — 通过大小、深浅区分层次
- **Internal structure** — 大模块内显示子组件结构
- **Consistent color coding** — 统一的3-4色方案
- **Professional polish** — 精致但不夸张

#### DON'T (不要有):
- ❌ Rainbow/multi-color gradients (彩虹渐变)
- ❌ Heavy drop shadows (重阴影)
- ❌ 3D effects / perspective (3D效果)
- ❌ Glowing effects (发光效果)
- ❌ Excessive decorative icons (过多装饰图标)
- ❌ Plain boring rectangles (完全平淡的方块)

#### 理想效果：
像顶会论文中精心设计的架构图 — 专业、清晰、有适度的视觉吸引力

## Figure Type
[Architecture Diagram / Pipeline / Comparison / etc.]

## Components to Include (BE SPECIFIC ABOUT CONTENT)
1. [Component 1]:
   - Label: "[exact text]"
   - Sub-label: "[smaller text below]"
   - Position: [left/center/right, top/middle/bottom]
   - Style: [border color, fill, internal structure]
2. [Component 2]: ...

## Layout
- Direction: [left-to-right / top-to-bottom]
- Spacing: [tight / normal / loose]
- Grouping: [how components should be grouped]

## Connections (BE EXPLICIT ABOUT DIRECTION)
EXACT arrow specifications:
1. [Component A] → [Component B]: Arrow goes FROM A TO B, label it "[data type]"
2. [Component C] → [Component D]: Arrow goes FROM C TO D, label it "[data type]"
...
VERIFY: Each arrow must point to the CORRECT target!

## Style Requirements (CVPR/ICLR/NeurIPS Standard)

### Visual Style
- Color palette: Professional academic colors
  - Inputs: Green (#10B981)
  - Encoders: Blue (#2563EB)
  - Fusion modules: Purple (#7C3AED)
  - Outputs: Orange (#EA580C)
- Font: Sans-serif (Arial/Helvetica), minimum 14pt, bold for labels
- Background: Clean white, no patterns
- Blocks: Rounded rectangles (8-12px radius), subtle gradient fill, colored border (2-3px)
- Subtle shadows for depth effect
- Print-friendly (must work in grayscale)

### CRITICAL: Arrow & Data Flow Requirements
1. **ALL arrows must be VERY THICK** - minimum 5-6px stroke width
2. **ALL arrows must have CLEAR arrowheads** - large, visible triangular heads
3. **ALL arrows must be BLACK or DARK GRAY** - not colored
4. **Label EVERY arrow** with what data flows through it
5. **VERIFY arrow direction** - each arrow MUST point to the correct target
6. **No ambiguous connections** - every arrow should have a clear source and destination

### Logic Clarity Requirements
1. **Data flow must be immediately obvious** - viewer should understand the pipeline in 5 seconds
2. **No crossing arrows** - reorganize layout to avoid arrow crossings
3. **Consistent direction** - maintain left-to-right or top-to-bottom flow throughout
4. **Group related components** - use subtle background boxes or spacing to group modules
5. **Clear hierarchy** - main components larger, sub-components smaller

## Additional Requirements
[Any specific requirements from user]
```

### Step 2: Gemini Layout Optimization (gemini-3-pro)

**Claude sends the initial prompt to Gemini (gemini-3-pro) for layout optimization.**

```bash
#!/bin/bash
# Step 2: Optimize layout using Gemini gemini-3-pro
# This step refines component positioning and spacing

set -e

OUTPUT_DIR="figures/ai_generated"
mkdir -p "$OUTPUT_DIR"

API_KEY="${GEMINI_API_KEY}"
URL="https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-preview:generateContent?key=$API_KEY"

# The initial prompt from Claude
INITIAL_PROMPT='[Claude fills in the detailed prompt here]'

# Layout optimization request
LAYOUT_REQUEST="You are an expert in academic figure layout design for CVPR/NeurIPS papers.

Analyze this figure request and provide an OPTIMIZED LAYOUT DESCRIPTION:

$INITIAL_PROMPT

Provide:
1. **Optimized Component Positions**: Exact positions (left/center/right, top/middle/bottom) for each component
2. **Spacing Recommendations**: Specific spacing between components
3. **Grouping Strategy**: Which components should be visually grouped together
4. **Arrow Routing**: Optimal paths for arrows to avoid crossings
5. **Visual Hierarchy**: Size recommendations for main vs sub-components

Output a DETAILED layout specification that will be used for rendering."

# Build JSON payload
python3 << PYTHON
import json
payload = {
    "contents": [{"parts": [{"text": '''$LAYOUT_REQUEST'''}]}]
}
with open("/tmp/gemini_layout_request.json", "w") as f:
    json.dump(payload, f, indent=2)
print("Layout request created")
PYTHON

# Call Gemini gemini-3-pro-preview for layout optimization (DIRECT connection, no proxy)
RESPONSE=$(curl -s --max-time 90 \
  -X POST "$URL" \
  -H 'Content-Type: application/json' \
  -d @/tmp/gemini_layout_request.json)

# Extract layout description
LAYOUT_DESCRIPTION=$(echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
try:
    print(data['candidates'][0]['content']['parts'][0]['text'])
except:
    print('Error extracting layout')
")

echo "=== Layout Optimization Complete ==="
echo "$LAYOUT_DESCRIPTION"
echo "$LAYOUT_DESCRIPTION" > "$OUTPUT_DIR/layout_description.txt"
```

