"""CI receipts must expose Unicode failures even under a narrow output locale."""
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET


def test_failure_annotation_retains_unicode_and_escapes_linebreaks_under_ascii_output(tmp_path):
    path = tmp_path / 'junit.xml'
    tree = ET.Element('testsuite')
    case = ET.SubElement(tree, 'testcase', classname='portability', name='中文路径')
    ET.SubElement(case, 'failure').text = '中文证据: 100%\nexpected != actual\r\n'
    ET.ElementTree(tree).write(path, encoding='utf-8', xml_declaration=True)
    tool = Path(__file__).resolve().parents[1] / 'tools/report_ci_failures.py'
    process = subprocess.run([sys.executable, '-B', str(tool), str(path)], capture_output=True,
        env=dict(os.environ, PYTHONIOENCODING='ascii'))
    assert process.returncode == 0, process.stderr
    stdout = process.stdout.decode('utf-8')
    assert '::error::portability.中文路径%0A中文证据: 100%25%0Aexpected != actual%0A' in stdout
    assert 'Pytest exit status remains' in stdout
    assert not process.stderr
