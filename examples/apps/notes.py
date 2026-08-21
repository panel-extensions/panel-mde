"""
A small note-taking app: pick a note in the sidebar, edit it as markdown, and
watch it render live.

    panel serve examples/apps/notes.py --dev
"""

import panel as pn
import panel_material_ui as pmui
import param

from panel_mde import MarkdownEditor

pn.extension()

NOTES = {
    "Release checklist": """
# Release checklist

| Step | Owner | Done |
| ---- | ----- | ---- |
| Tag the release | maintainer | yes |
| Build the wheel | CI | yes |
| Publish to PyPI | CI | no |

- [x] Changelog written
- [ ] Announcement drafted
""".lstrip(),
    "Meeting notes": """
## Meeting notes

**Attendees:** everyone who could make it.

1. Reviewed the roadmap
2. Agreed to ship the editor first
3. Parked the upload flow for now

> Storing markdown rather than HTML means every surface agrees on one format.
""".lstrip(),
    "Scratch": "",
}


class Notes(param.Parameterized):
    """Keeps the editor and the note store in sync as the selection changes."""

    note = param.Selector(objects=list(NOTES), default="Release checklist")

    def __init__(self, **params):
        super().__init__(**params)
        self.notes = dict(NOTES)
        self.editor = MarkdownEditor(
            value=self.notes[self.note],
            placeholder="Write something in markdown...",
            preview=True,
            status_bar=True,
            sizing_mode="stretch_both",
        )
        self.editor.param.watch(self._store, "value")

    @param.depends("note", watch=True)
    def _load(self):
        self.editor.value = self.notes[self.note]

    def _store(self, event):
        self.notes[self.note] = event.new


notes = Notes()

note_select = pmui.Select.from_param(notes.param.note, label="Note")
preview = pmui.Switch.from_param(notes.editor.param.preview, label="Live preview")
location = pmui.RadioButtonGroup.from_param(
    notes.editor.param.preview_location, label="Preview position",
    disabled=notes.editor.param.preview.rx.not_(),
)
line_numbers = pmui.Switch.from_param(notes.editor.param.line_numbers, label="Line numbers")


def outline(text):
    """The point of a markdown-native value: the source itself is queryable."""
    headings = [line for line in text.splitlines() if line.startswith("#")]
    if not headings:
        return "#### Outline\n\n_No headings yet._"
    items = "\n".join(
        f"{'  ' * (len(line) - len(line.lstrip('#')) - 1)}- {line.lstrip('# ')}"
        for line in headings
    )
    return f"#### Outline\n\n{items}"


outline_pane = pn.pane.Markdown(notes.editor.param.value_input.rx.pipe(outline), margin=(0, 10))

pmui.Page(
    title="Markdown notes",
    sidebar=[
        note_select, pmui.Divider(), preview, location, line_numbers,
        pmui.Divider(), outline_pane,
    ],
    main=[notes.editor],
    sidebar_width=280,
).servable()
