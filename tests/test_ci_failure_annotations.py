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


def test_long_trace_keeps_final_exception_in_public_annotation_excerpt(tmp_path):
    path = tmp_path / 'junit.xml'
    tree = ET.Element('testsuite')
    case = ET.SubElement(tree, 'testcase', classname='checkpoint', name='test_publish')
    cause = 'OSError: [Errno 9] Bad file descriptor; 原始异常'
    ET.SubElement(case, 'error').text = ('fixture setup\n' + 'stack frame 中文\n' * 1000
                                       + cause + '\n')
    ET.SubElement(tree, 'testcase', classname='checkpoint', name='test_completed')
    skipped = ET.SubElement(tree, 'testcase', classname='checkpoint', name='test_optional')
    ET.SubElement(skipped, 'skipped')
    ET.ElementTree(tree).write(path, encoding='utf-8', xml_declaration=True)
    tool = Path(__file__).resolve().parents[1] / 'tools/report_ci_failures.py'
    process = subprocess.run([sys.executable, '-B', str(tool), str(path)], capture_output=True,
                             env=dict(os.environ, PYTHONIOENCODING='ascii'))
    assert process.returncode == 0, process.stderr
    stdout = process.stdout.decode('utf-8')
    annotations = [line.removeprefix('::error::') for line in stdout.splitlines()
                   if line.startswith('::error::')]
    assert len(annotations) == 1
    # Simulate the runner's decoded, bounded public message, including Unicode.
    message = annotations[0].replace('%0D', '\r').replace('%0A', '\n').replace('%25', '%')
    assert len(message.encode('utf-8')) <= 4000
    assert message.startswith('checkpoint.test_publish\nfixture setup\n')
    assert cause in message and 'final exception retained' in message
    assert 'Pytest JUnit receipt: 1 passed, 1 skipped, 0 failed, 1 errors.' in stdout
    assert 'Pytest exit status remains' in stdout
    assert not process.stderr
