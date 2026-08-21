"""
Appending to the document from outside the editor while the user is typing in
it. Upload an image and its reference is added at the end of the note without
moving the caret, losing the selection, scrolling away or clearing undo.

    panel serve examples/apps/image_upload.py --dev
"""

import base64

import panel as pn
import panel_material_ui as pmui

from panel_mde import MarkdownEditor

pn.extension()

INTRO = """
# Trip report

Put the caret somewhere in the middle of this sentence, or select a few words,
then upload an image with the button in the sidebar. Keep typing afterwards:
nothing you were doing was disturbed.

## Details

The reference definition is appended at the end of the document, so the note
itself stays readable no matter how long the URL is.
""".lstrip()

editor = MarkdownEditor(
    value=INTRO,
    preview=True,
    autofocus=True,
    sizing_mode="stretch_both",
)

upload = pmui.FileInput(
    label="Upload an image",
    accept=".png,.jpg,.jpeg,.gif,.svg",
    icon="image",
    sizing_mode="stretch_width",
)
log = pn.pane.Markdown("", margin=(0, 10))


def add_image(event):
    if not event.new:
        return
    # A real app would store the bytes and reference a URL; a data URI keeps
    # this example self-contained without a static route.
    uri = f"data:{upload.mime_type};base64,{base64.b64encode(event.new).decode()}"
    label = upload.filename.rsplit(".", 1)[0]
    ref = f"img-{len(editor.value.splitlines())}"

    # Reference-style so the body of the note stays short and legible.
    editor.value += f"\n\n![{label}][{ref}]\n\n[{ref}]: {uri}\n"
    log.object = f"Added `{upload.filename}` as `[{ref}]`"


upload.param.watch(add_image, "value")

pmui.Page(
    title="Append while editing",
    sidebar=[upload, pmui.Divider(), log],
    main=[editor],
    sidebar_width=280,
).servable()
