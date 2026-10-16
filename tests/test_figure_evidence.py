"""Figures remain bound to data and reject invalid geometry before rendering."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

from tools.figure_evidence import build_manifest, check_manifest

ROOT = Path(__file__).resolve().parents[1]
module_spec = importlib.util.spec_from_file_location('canonical_figure_renderer', ROOT / 'skills/figure-spec/scripts/figure_renderer.py')
renderer = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(renderer)


@pytest.fixture
def recipe(tmp_path):
    (tmp_path / 'data.csv').write_text('unit,value\na,"3"\nb,"5"\nc,\n', encoding='utf-8')
    (tmp_path / 'plot.py').write_text('# Editable source with the chosen aggregation\n', encoding='utf-8')
    (tmp_path / 'out.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding='utf-8')
    return {'schema_version': 1, 'kind': 'data', 'caption': 'Observed values; one observation is missing.',
            'inputs': ['data.csv'], 'source': 'plot.py', 'outputs': ['out.svg'],
            'transforms': {'selection': 'all planned units', 'aggregation': 'none', 'unit': 'score',
                           'uncertainty': 'not estimated', 'axis': 'linear', 'smoothing': 'none',
                           'missing': 'shown as missing, not zero'}}


@pytest.mark.parametrize('path', ['data.csv', 'plot.py', 'out.svg'])
def test_manifest_detects_changed_data_source_or_render(tmp_path, recipe, path):
    record = build_manifest(tmp_path, recipe)
    assert check_manifest(tmp_path, record)['status'] == 'PASS'
    (tmp_path / path).write_text('changed', encoding='utf-8')
    with pytest.raises(ValueError):
        check_manifest(tmp_path, record)


def test_literal_numeric_check_is_reported_without_claiming_semantic_support(tmp_path, recipe):
    recipe['numeric_claims'] = [{'value': '3', 'source': 'data.csv'}, {'value': '99', 'source': 'data.csv'}]
    record = build_manifest(tmp_path, recipe)
    assert record['numeric_checks']['summary'] == {'verified': 1, 'value_not_found': 1}
    assert 'scientific' in record['scope']


@pytest.mark.parametrize('field', ['unit', 'aggregation', 'uncertainty', 'missing'])
def test_data_manifest_needs_explicit_statistical_display_recipe(tmp_path, recipe, field):
    recipe['transforms'][field] = ''
    with pytest.raises(ValueError, match=field):
        build_manifest(tmp_path, recipe)


def test_output_cannot_be_original_data_and_paths_cannot_escape(tmp_path, recipe):
    recipe['outputs'] = ['data.csv']
    with pytest.raises(ValueError, match='overwrite'):
        build_manifest(tmp_path, recipe)


def test_output_alias_cannot_relabel_data_as_a_generated_figure(tmp_path, recipe):
    recipe['outputs'] = ['./data.csv']
    with pytest.raises(ValueError, match='overwrite'):
        build_manifest(tmp_path, recipe)
    recipe['outputs'] = ['out.svg']; recipe['inputs'] = ['../data.csv']
    with pytest.raises(ValueError):
        build_manifest(tmp_path, recipe)


def spec():
    return {'canvas': {'width': 500, 'height': 200}, 'nodes': [
        {'id': 'a', 'label': '问题 <A>', 'x': 100, 'y': 100},
        {'id': 'b', 'label': 'Evidence', 'x': 350, 'y': 100}],
        'edges': [{'from': 'a', 'to': 'b'}]}


@pytest.mark.parametrize('change', [
    {'nodes': [3]}, {'nodes': [{'id': [], 'x': 1, 'y': 2}]},
    {'nodes': [{'id': 'x', 'x': float('nan'), 'y': 2}]},
    {'canvas': {'width': float('inf')}}, {'labels': [{'x': 'left'}]},
    {'edges': [5]}, {'groups': [5]},
])
def test_malformed_geometry_returns_diagnostics_without_crashing(change):
    value = spec(); value.update(change)
    assert any(issue.startswith('CRITICAL:') for issue in renderer.validate_spec(value))


def test_renderer_is_deterministic_editable_and_legacy_entrypoint_still_works(tmp_path):
    value = spec()
    assert not any(issue.startswith('CRITICAL:') for issue in renderer.validate_spec(value))
    result = renderer.render_svg(value)
    assert result == renderer.render_svg(copy.deepcopy(value))
    ET.fromstring(result)
    assert '问题 &lt;A&gt;' in result
    source = tmp_path / 'spec.json'; source.write_text(json.dumps(value), encoding='utf-8')
    output = tmp_path / 'legacy.svg'
    run = subprocess.run([sys.executable, str(ROOT / 'tools/figure_renderer.py'), 'render',
                          str(source), '--output', str(output)], capture_output=True)
    assert run.returncode == 0, run.stderr
    assert output.read_text(encoding='utf-8') == result
