"""Read entrypoints and their explicitly deferred workflow instructions."""
from pathlib import Path
import re

LINK = re.compile(r'\]\((references/workflow-[a-z0-9-]+\.md)\)')
WORKFLOW_MARK = '<!-- EI-WORKFLOW-REFERENCE -->'


def workflow_paths(entrypoint):
    """Return ordered, existing stage documents linked by this entrypoint."""
    entrypoint = Path(entrypoint)
    paths = [entrypoint]
    for relative in dict.fromkeys(LINK.findall(entrypoint.read_text(encoding='utf-8'))):
        document = entrypoint.parent / relative
        if not document.read_text(encoding='utf-8').startswith(WORKFLOW_MARK):
            raise ValueError(f'Expected a deferred skill instruction document: {document}')
        paths.append(document)
    return paths


def read_workflow(entrypoint):
    """Join the entrypoint and its planned stages for static contract checks."""
    return '\n\n'.join(path.read_text(encoding='utf-8') for path in workflow_paths(entrypoint))
