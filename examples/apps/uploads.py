"""
Getting files and text into a note from outside the editor.

Paste an image from the clipboard or drag a file onto the editor and
`upload_handler` receives the bytes, stores them and returns a URL, which the
editor turns into an image reference or a media tag. The sidebar button appends
to `value` from Python instead, which is the other way content arrives: neither
disturbs the person typing.

    panel serve examples/apps/uploads.py --static-dirs media=examples/apps/media --dev
"""

import asyncio
import datetime as dt
import re

from hashlib import sha1
from pathlib import Path

import panel as pn
import panel_material_ui as pmui

from panel_mde import MarkdownEditor

pn.extension()

MEDIA = Path(__file__).parent / "media"
MEDIA.mkdir(exist_ok=True)

INTRO = """
# Trip report

Paste an image from the clipboard or drag a file onto this note. Keep typing
while it uploads: a marker holds the spot, so the file lands where you dropped
it rather than wherever the caret has moved on to.

## Details

Nothing is inserted until the handler returns, so `value` never holds a
half-finished reference.
""".lstrip()

FILETYPES = {
    "Images only": ["image/*"],
    "Images, video and audio": ["image/*", "video/*", "audio/*"],
    "Anything": [],
}

MAX_SIZE = 5_000_000

filetypes = pmui.Select(
    label="Accepted files", options=list(FILETYPES),
    value="Images, video and audio", sizing_mode="stretch_width",
)
slow = pmui.Switch(label="Simulate slow storage", value=False)
log = pn.pane.Markdown("_Nothing uploaded yet._", margin=(0, 10))
uploaded = []


async def store(file):
    """Store a pasted or dropped file and return the URL to reference it by."""
    if slow.value:
        await asyncio.sleep(2)
    # A real app writes to object storage; this writes next to the app and lets
    # the Panel server hand it back out of --static-dirs. Digesting the contents
    # keeps two pastes of the same clipboard image from turning into two files,
    # and two different files from sharing a name.
    stem, _, suffix = file.name.rpartition(".")
    name = re.sub(r"[^\w.-]+", "-", f"{stem or file.name}-{sha1(file.data).hexdigest()[:8]}")
    path = MEDIA / (f"{name}.{suffix}" if suffix and stem else name)
    path.write_bytes(file.data)
    uploaded.append(f"- `{path.name}` &mdash; {file.mime_type}, {file.size / 1000:,.0f} kB")
    log.object = "\n".join(uploaded)
    return f"/media/{path.name}"


editor = MarkdownEditor(
    value=INTRO,
    upload_handler=store,
    accepted_filetypes=filetypes.param.value.rx.pipe(FILETYPES.get),
    max_upload_size=MAX_SIZE,
    preview=True,
    status_bar=True,
    autofocus=True,
    sizing_mode="stretch_both",
)

append = pmui.Button(
    label="Append a section", icon="playlist_add",
    variant="outlined", sizing_mode="stretch_width",
)


def append_section(event):
    # Writing `value` applies the smallest edit that produces the new text, so
    # the caret, the selection, the scroll position and undo all survive.
    stamp = dt.datetime.now().strftime("%H:%M:%S")
    editor.value += f"\n\n## Added at {stamp}\n\nWritten from Python while you were typing.\n"


append.on_click(append_section)

pmui.Page(
    title="Pasting, dropping and appending",
    sidebar=[
        pmui.Typography(f"Files are capped at {MAX_SIZE // 1_000_000}MB.", variant="body2"),
        filetypes, slow, pmui.Divider(), append, pmui.Divider(), log,
    ],
    main=[editor],
    sidebar_width=300,
).servable()
