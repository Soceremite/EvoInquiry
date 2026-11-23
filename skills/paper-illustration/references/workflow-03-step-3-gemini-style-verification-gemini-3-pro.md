<!-- EI-WORKFLOW-REFERENCE -->

# Step 3: Gemini Style Verification (gemini-3-pro)

Read this file when the workflow reaches Step 3: Gemini Style Verification (gemini-3-pro) through Step 4: Paperbanana Image Rendering (gemini-3-pro-image-preview). In commands and examples, interpret relative skill paths from the entrypoint directory.

### Step 3: Gemini Style Verification (gemini-3-pro)

**Claude sends the optimized layout to Gemini for CVPR/NeurIPS style verification.**

```bash
#!/bin/bash
# Step 3: Verify and enhance style compliance using Gemini gemini-3-pro

API_KEY="${GEMINI_API_KEY}"
URL="https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-preview:generateContent?key=$API_KEY"

# Read layout from previous step
LAYOUT=$(cat figures/ai_generated/layout_description.txt)

# Style verification request
STYLE_REQUEST="You are a CVPR/NeurIPS paper figure reviewer specializing in visual standards.

Review and ENHANCE this figure specification for top-tier conference compliance:

$LAYOUT

Ensure compliance with:
1. **Color Palette**: Use professional academic colors (green for inputs, blue for encoders, purple for fusion, orange for outputs)
2. **Arrow Standards**: Thick (5-6px), black/dark gray, clear arrowheads, all labeled
3. **Font Standards**: Sans-serif, minimum 14pt, readable in print
4. **Visual Appeal (科研风格)**:
   - ✅ Subtle same-color gradients, rounded corners (6-10px), internal structure visible
   - ❌ NO heavy shadows, NO glowing effects, NO rainbow gradients

Output an ENHANCED figure specification with explicit style instructions for rendering."

# Build JSON payload
python3 << PYTHON
import json
payload = {
    "contents": [{"parts": [{"text": '''$STYLE_REQUEST'''}]}]
}
with open("/tmp/gemini_style_request.json", "w") as f:
    json.dump(payload, f, indent=2)
print("Style request created")
PYTHON

# Call Gemini gemini-3-pro-preview for style verification (DIRECT connection, no proxy)
RESPONSE=$(curl -s --max-time 90 \
  -X POST "$URL" \
  -H 'Content-Type: application/json' \
  -d @/tmp/gemini_style_request.json)

# Extract style-enhanced specification
STYLE_SPEC=$(echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
try:
    print(data['candidates'][0]['content']['parts'][0]['text'])
except:
    print('Error extracting style spec')
")

echo "=== Style Verification Complete ==="
echo "$STYLE_SPEC"
echo "$STYLE_SPEC" > "figures/ai_generated/style_spec.txt"
```

### Step 4: Paperbanana Image Rendering (gemini-3-pro-image-preview)

**Claude sends the optimized, style-verified specification to Paperbanana for rendering.**

```bash
#!/bin/bash
# Step 4: Render image using Paperbanana (gemini-3-pro-image-preview)
# Internal codename: Nano Banana Pro
# Use DIRECT connection (no proxy) - proxy causes SSL errors

set -e

OUTPUT_DIR="figures/ai_generated"
mkdir -p "$OUTPUT_DIR"

API_KEY="${GEMINI_API_KEY}"
URL="https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent?key=$API_KEY"

# Read the style-enhanced specification from previous step
STYLE_SPEC=$(cat figures/ai_generated/style_spec.txt)

# Add rendering instructions
RENDER_PROMPT="Render a publication-quality academic diagram based on this specification:

$STYLE_SPEC

RENDERING REQUIREMENTS:
- Output a clean, professional diagram suitable for CVPR/NeurIPS submission
- Use vector-quality rendering with sharp edges and clear text
- Ensure all elements are properly aligned and spaced
- The diagram should be immediately understandable at a glance"

# Build JSON payload using Python for proper escaping
python3 << PYTHON
import json
payload = {
    "contents": [{"parts": [{"text": '''$RENDER_PROMPT'''}]}],
    "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
}
with open("/tmp/gemini_request.json", "w") as f:
    json.dump(payload, f, indent=2)
print("JSON payload created")
PYTHON

# Call Paperbanana API WITHOUT proxy (direct connection works better)
RESPONSE=$(curl -s --max-time 180 \
  -X POST "$URL" \
  -H 'Content-Type: application/json' \
  -d @/tmp/gemini_request.json)

# Check for error
if echo "$RESPONSE" | grep -q '"error"'; then
    echo "API Error:"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
    exit 1
fi

# Extract and save image
echo "$RESPONSE" | python3 << 'PYTHON'
import sys, json, base64
from pathlib import Path

output_dir = Path("figures/ai_generated")
data = json.load(sys.stdin)

try:
    parts = data['candidates'][0]['content']['parts']
    iteration = 1  # Claude increments this each iteration

    for part in parts:
        if 'text' in part:
            print(f"\n[Paperbanana]: {part['text'][:200]}...")
        elif 'inlineData' in part:
            img_data = base64.b64decode(part['inlineData']['data'])
            img_path = output_dir / f"figure_v{iteration}.png"
            with open(img_path, "wb") as f:
                f.write(img_data)
            print(f"\n✅ Image saved: {img_path}")
            print(f"   Size: {len(img_data)/1024:.1f} KB")

except Exception as e:
    print(f"Parse error: {e}")
    print(f"Raw response: {str(data)[:500]}")
PYTHON
```

