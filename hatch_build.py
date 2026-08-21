from __future__ import annotations

import os
import sys
import typing as t
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

BASE_DIR = Path(__file__).parent
GREEN, RED, RESET = "\033[0;32m", "\033[0;31m", "\033[0m"


def compile_bundle():
    from panel.io.compile import compile_components, find_module_bundles

    print(f"{GREEN}[PANEL-MDE]{RESET} Compile panel-mde bundle", flush=True)

    sys.path.insert(0, str(BASE_DIR / "src"))
    module_bundles = find_module_bundles('panel_mde')
    errors = 0
    for bundle, components in module_bundles.items():
        # Not verbose: that runs esbuild at --log-level=debug, which reports the
        # Node-only `require` in typo-js (EasyMDE's spell-check dictionary
        # loader) as an indirect-require note. It is inert in a browser bundle.
        ret = compile_components(
            components,
            outfile=bundle,
            verbose=False,
        )
        if ret is None:
            errors += 1
        else:
            errors += ret
    if sys.platform != "win32":
        # npm can cause non-blocking stdout; so reset it just in case
        import fcntl

        flags = fcntl.fcntl(sys.stdout, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdout, fcntl.F_SETFL, flags & ~os.O_NONBLOCK)

    if not errors:
        print(f"{GREEN}[PANEL-MDE]{RESET} Finished building bundle", flush=True)
    else:
        print(f"{RED}[PANEL-MDE]{RESET} Failed building bundle", flush=True)
        sys.exit(1)


class BuildHook(BuildHookInterface):
    """The hatch build hook."""

    PLUGIN_NAME = "install"

    def initialize(self, version: str, build_data: dict[str, t.Any]) -> None:
        """Initialize the plugin."""
        if self.target_name not in ["wheel", "sdist"]:
            return

        compile_bundle()
