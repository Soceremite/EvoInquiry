#!/usr/bin/env python3
"""Rebuild README workflow SVGs with EvoInquiry's existing FigureSpec renderer."""
from __future__ import annotations

import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ASSETS = Path(__file__).resolve().parent
ROOT = ASSETS.parents[1]
SVG = 'http://www.w3.org/2000/svg'


def characters() -> dict[str, ET.Element]:
    root = ET.parse(ASSETS / 'characters.svg').getroot()
    return {group.get('id'): group for group in root.findall(f'{{{SVG}}}defs/{{{SVG}}}g')}


def stamp_character(svg: ET.Element, sprites: dict, name: str,
                    x: float, y: float, scale: float) -> None:
    wrapper = ET.SubElement(svg, f'{{{SVG}}}g', {
        'transform': f'translate({x} {y}) scale({scale})',
        'aria-hidden': 'true',
    })
    ET.SubElement(wrapper, f'{{{SVG}}}ellipse', {
        'cx': '35', 'cy': '105', 'rx': '40', 'ry': '5', 'fill': '#E5DCCB',
    })
    wrapper.append(deepcopy(sprites[name]))


def decorate(svg: ET.Element, sprites: dict, name: str) -> None:
    placements = {
        'research-loop': [('reader', 112, 573, .5), ('reviewer', 680, 573, .5),
                          ('runner', 1275, 573, .5)],
        'fair-comparison': [('reader', 104, 278, .5), ('runner', 795, 278, .5),
                            ('reviewer', 1018, 278, .5)],
        'evidence-archive': [('reviewer', 854, 162, .55), ('reader', 1305, 548, .5)],
    }
    for character, x, y, scale in placements[name]:
        stamp_character(svg, sprites, character, x, y, scale)
    ET.SubElement(svg, f'{{{SVG}}}path', {
        'd': 'M1337 105L1342 114L1351 119L1342 124L1337 133L1332 124L1323 119L1332 114Z',
        'fill': '#FFD95E', 'stroke': '#D5B24A', 'stroke-width': '1.5',
        'aria-hidden': 'true',
    })


def write_svg(svg: ET.Element, target: Path) -> None:
    ET.indent(svg, space='  ')
    target.write_text(ET.tostring(svg, encoding='unicode') + '\n', encoding='utf-8')
    print(target.relative_to(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gif', action='store_true', help='Also export the animated cover (Pillow and an SVG rasterizer required)')
    args = parser.parse_args()
    source = ROOT / 'skills/figure-spec/scripts/figure_renderer.py'
    module_spec = importlib.util.spec_from_file_location('evo_readme_figure_renderer', source)
    if module_spec is None or module_spec.loader is None:
        raise SystemExit(f'Cannot load FigureSpec renderer: {source}')
    renderer = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(renderer)
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    sprites = characters()
    for path in sorted((ASSETS / 'specs').glob('*.json')):
        spec = json.loads(path.read_text(encoding='utf-8'))
        issues = renderer.validate_spec(spec)
        if issues:
            raise SystemExit(f'{path.name}: ' + '; '.join(issues))
        svg = ET.fromstring(renderer.render_svg(spec))
        title_id = f'{path.stem}-title'
        svg.set('role', 'img')
        svg.set('aria-labelledby', title_id)
        title = ET.Element('{http://www.w3.org/2000/svg}title', {'id': title_id})
        title.text = spec['title']
        svg.insert(0, title)
        for text in svg.iter('{http://www.w3.org/2000/svg}text'):
            if text.get('fill') in ('#888888', '#999999'):
                text.set('fill', '#6A637D')
        for rectangle in svg.iter(f'{{{SVG}}}rect'):
            if rectangle.get('rx') == '8':
                rectangle.set('rx', '20')
        decorate(svg, sprites, path.stem)
        target = ASSETS / f'{path.stem}.svg'
        write_svg(svg, target)
    hero = ET.parse(ASSETS / 'specs/hero.svg').getroot()
    for group in hero.iter(f'{{{SVG}}}g'):
        character = group.get('data-character')
        if character:
            group.append(deepcopy(sprites[character]))
    write_svg(hero, ASSETS / 'evo-inquiry-hero.svg')
    if args.gif:
        from animate import export_gif
        export_gif(ASSETS / 'evo-inquiry-hero.svg', ASSETS / 'evo-inquiry-hero.gif')


if __name__ == '__main__':
    main()
