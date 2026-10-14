# EvoInquiry README visuals

Four pastel illustrations explain EvoInquiry's research workflows. Cream,
mint, lavender and coral colours accompany a tiny pixel research team.
The static SVGs render without external fonts, scripts or API calls.

| Image | Purpose | Editable source |
| --- | --- | --- |
| [Animated banner](evo-inquiry-hero.gif) / [static banner](evo-inquiry-hero.svg) | Researchers ask, test and learn in an evolving loop | [Hero SVG template](specs/hero.svg) + [characters](characters.svg) |
| [Research workflow](research-loop.svg) | Six stages, revision loops and project continuation | [FigureSpec](specs/research-loop.json) |
| [Fair comparison](fair-comparison.svg) | Controlled contribution, equal resource budget and tuned performance | [FigureSpec](specs/fair-comparison.json) |
| [Evidence before archival](evidence-archive.svg) | Retained experiment records and validation-selected weights | [FigureSpec](specs/evidence-archive.json) |

Rebuild all four static illustrations from the repository root:

```sh
python docs/assets/render.py
```

The build uses the existing `figure-spec` renderer and Python's standard
library. Edit the JSON specifications, hero template or character sprites, then rebuild.
The generated SVGs include accessible titles and explicit background colours
for readable GitHub rendering in light and dark themes.

To rebuild the animated cover, use an environment with Pillow and CairoSVG
(or existing system librsvg/cairo libraries):

```sh
python docs/assets/render.py --gif
```

The GIF uses 48 frames in a six-second loop at 1080 × 420 pixels. Only the
illustration moves: characters gently float, one waves and a star softly pulses.
Text and the three flow diagrams stay still. The README includes a static
cover link and a reduced-motion source for renderers that support it.
GIF rasterization is optional; ordinary SVG regeneration uses only the standard library.

These images describe implemented capabilities; they contain no illustrative
benchmark numbers, claims of guaranteed novelty or automatic skill-selection
rates. File coverage and hash validation are separate from scientific review.
The comparison-archive diagram describes the optional local helper.
