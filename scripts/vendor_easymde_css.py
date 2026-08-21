"""Refresh the vendored EasyMDE stylesheet from npm.

The editor's JavaScript is bundled by ``panel compile``, but its stylesheet
has to be checked in: ``_stylesheets`` must resolve in every mode Panel
supports (compiled server session, notebook, pyodide *and* the uncompiled
``--dev`` loop, where a bare ``import "easymde/dist/easymde.min.css"`` would
not resolve in the browser). Vendoring keeps one file that works everywhere.

Run with ``pixi run vendor-css`` after bumping ``EASYMDE_VERSION``.
"""

from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

REPO = pathlib.Path(__file__).parent.parent
BASE = REPO / "src" / "panel_mde"
TARGET = BASE / "models" / "easymde.css"

MEMBER = "package/dist/easymde.min.css"

HEADER = """\
/*
 * Vendored from easymde@{version} (dist/easymde.min.css), MIT licensed.
 * https://github.com/Ionaru/easy-markdown-editor
 *
 * DO NOT EDIT. Regenerate with `pixi run vendor-css` after bumping
 * EASYMDE_VERSION in src/panel_mde/base.py. Panel-specific overrides
 * belong in models/mde.css instead.
 *
 * easymde-version: {version}
 */
"""


def pinned_version() -> str:
    source = (BASE / "base.py").read_text(encoding="utf-8")
    match = re.search(r'^EASYMDE_VERSION = "([^"]+)"', source, re.MULTILINE)
    if match is None:
        raise SystemExit("Could not find EASYMDE_VERSION in base.py")
    return match.group(1)


def main() -> int:
    version = pinned_version()
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = pathlib.Path(tmp)
        subprocess.run(
            ["npm", "pack", f"easymde@{version}", "--silent"],
            cwd=tmpdir, check=True, capture_output=True, text=True,
        )
        (tarball,) = tmpdir.glob("*.tgz")
        with tarfile.open(tarball) as tar:
            member = tar.extractfile(MEMBER)
            if member is None:
                raise SystemExit(f"{MEMBER} missing from {tarball.name}")
            css = member.read().decode("utf-8")

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(HEADER.format(version=version) + css.strip() + "\n", encoding="utf-8")
    print(f"Vendored easymde@{version} stylesheet -> {TARGET.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    if shutil.which("npm") is None:
        raise SystemExit("npm is required to refresh the vendored stylesheet")
    sys.exit(main())
