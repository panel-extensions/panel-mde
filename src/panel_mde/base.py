"""Shared bundle and asset plumbing for panel-mde components."""

from __future__ import annotations

import pathlib

from bokeh.embed.bundle import extension_dirs
from panel.custom import JSComponent
from panel.io.resources import EXTENSION_CDN
from panel.util import base_version

from .__version import __version__

BASE_PATH = pathlib.Path(__file__).parent
DIST_PATH = BASE_PATH / "dist"
MODELS_PATH = BASE_PATH / "models"

IS_RELEASE = __version__ == base_version(__version__)
CDN_BASE = f"https://cdn.holoviz.org/panel-mde/v{base_version(__version__)}"
CDN_DIST = f"{CDN_BASE}/panel-mde.bundle.js"

# Every Bokeh-based server serves extension_dirs at
# /static/extensions/<name>/, so registering here keeps the asset wiring
# inside the package that needs it, independent of the serving entrypoint.
extension_dirs["panel-mde"] = DIST_PATH
EXTENSION_CDN[DIST_PATH] = CDN_BASE

#: Pinned EasyMDE release. The JavaScript is compiled into the bundle by
#: ``panel compile``; the stylesheet is vendored alongside it by
#: ``scripts/vendor_easymde_css.py``. Bump both together.
EASYMDE_VERSION = "2.21.0"


class MDEditorComponent(JSComponent):
    """
    Baseclass for components wrapping EasyMDE.

    Declares the compiled bundle location, the JS dependency that
    ``panel compile`` resolves into a ``package.json``, and the vendored
    stylesheets. Nothing here is fetched from a third-party CDN at runtime:
    the bundle is served same-origin out of ``dist/`` and both stylesheets
    are files inside the package.
    """

    _bundle = DIST_PATH / "panel-mde.bundle.js"

    _importmap = {
        "imports": {
            "easymde": f"https://esm.sh/easymde@{EASYMDE_VERSION}",
        }
    }

    # easymde.css is vendored rather than imported from the ESM so that it
    # also resolves in the uncompiled `--dev` loop, in notebooks and under
    # pyodide. mde.css layers Panel-specific layout on top.
    _stylesheets = [
        MODELS_PATH / "easymde.css",
        MODELS_PATH / "mde.css",
    ]

    _render_policy = "manual"

    __abstract = True


__all__ = ["MDEditorComponent"]
