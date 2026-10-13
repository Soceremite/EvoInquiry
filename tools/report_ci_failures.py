#!/usr/bin/env python3
"""Expose pytest failures as CI annotations while preserving the test exit status.

This reads a JUnit receipt; it does not rerun, skip or change any test. Public
annotations let maintainers diagnose cross-platform failures without a log token.
"""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


def escape(value):
    return value.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')


def main():
    # GitHub consumes UTF-8 annotations, including Unicode paths and assertions.
    sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    path = Path(sys.argv[1])
    if not path.is_file():
        print('::warning::No pytest JUnit receipt was produced; inspect the failed test step.')
        return
    document = ET.parse(path)
    for case in document.iter('testcase'):
        for tag in ('failure', 'error'):
            for failure in case.findall(tag):
                name = '.'.join(filter(None, (case.get('classname'), case.get('name'))))
                detail = failure.text or failure.get('message', '')
                if len(detail) > 24000:
                    detail = detail[:8000] + '\n[receipt excerpt truncated]\n' + detail[-16000:]
                print('::error::' + escape(name + '\n' + detail))
    print('Pytest exit status remains the result of the original test step.')


if __name__ == '__main__':
    main()
