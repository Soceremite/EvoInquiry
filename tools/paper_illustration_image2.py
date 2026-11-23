#!/usr/bin/env python3
"""Legacy entry point — forwards to the canonical paper_illustration_image2.

The canonical implementation now lives at
    skills/paper-illustration-image2/scripts/paper_illustration_image2.py
(Phase 3.2 — Arch C — self-contained single-owner helper).

This shim keeps the four legacy resolver layers working without a
re-install:

  .ei/tools/paper_illustration_image2.py
       → $ARIS_REPO/tools/paper_illustration_image2.py (this shim)
       → $ARIS_REPO/skills/paper-illustration-image2/scripts/paper_illustration_image2.py

  tools/paper_illustration_image2.py (in-repo run)
       → this shim → canonical

  $ARIS_REPO/tools/paper_illustration_image2.py (env-var)
       → this shim → canonical

  Manual <project>/tools/paper_illustration_image2.py copies of the
  pre-Phase-3.2 file continue to work standalone (no shim semantics
  needed; the canonical script is self-contained).

The canonical helper receives its own script path and the forwarded arguments.
On Windows the shim waits for the helper and returns its exit status.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
REAL = REPO_ROOT / "skills" / "paper-illustration-image2" / "scripts" / "paper_illustration_image2.py"


def _fail(msg: str) -> int:
    sys.stderr.write(msg + "\n")
    return 1


def main() -> int:
    if not REAL.is_file():
        return _fail(
            f"ERROR: canonical paper_illustration_image2.py not found at {REAL}.\n"
            "       The Phase 3.2 migration moved this helper into the\n"
            "       /paper-illustration-image2 SKILL\n"
            "       ('skills/paper-illustration-image2/scripts/'). Your\n"
            "       local checkout may be incomplete — try `git pull` from the\n"
            "       ARIS repo, or rerun `bash tools/install_aris.sh` to refresh\n"
            "       the project-local symlink chain."
        )
    command = [sys.executable, str(REAL), *sys.argv[1:]]
    if os.name == "nt":
        return subprocess.call(command)
    os.execv(sys.executable, command)
    return 0  # unreachable; os.execv does not return on success


if __name__ == "__main__":
    sys.exit(main())
