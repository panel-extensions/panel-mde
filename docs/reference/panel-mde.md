# MarkdownEditor

A rich text editor whose value **is** markdown source. Formatting comes from a
toolbar, but nothing is ever converted to HTML behind your back, so what you
store is the same markdown you would have typed by hand.

```python
import panel as pn

from panel_mde import MarkdownEditor

pn.extension()

editor = MarkdownEditor(
    value="# Hello\n\nStart typing...",
    height=400,
)
editor.servable()
```

## Value

`value` holds the markdown source and updates on every keystroke, so a watcher
fires as the user types:

```python
editor.param.watch(lambda event: print(event.new), "value")
```

Set `on_keyup=False` to defer `value` until the editor loses focus or the user
presses <kbd>Ctrl</kbd>/<kbd>Cmd</kbd>+<kbd>Enter</kbd>, matching
`pn.widgets.TextInput`. `value_input` always tracks the live text regardless.

Writing `value` from Python applies the smallest edit that produces the new
text, so the caret, the selection, the scroll position and the undo history all
survive. That makes it safe to append to the document while the user is typing
in it:

```python
def add_image(event):
    editor.value += f"\n\n![{upload.filename}]({store(upload.value)})\n"

upload.param.watch(add_image, "value")
```

## Toolbar

`toolbar=True` (the default) shows a general-purpose set of actions. Pass a
list to choose your own, using `"|"` for a separator:

```python
MarkdownEditor(
    toolbar=["bold", "italic", "heading", "|",
             "unordered-list", "ordered-list", "table", "|",
             "link", "image", "|", "undo", "redo"],
)
```

`toolbar=False` hides it entirely. The available actions are:

| Action | Effect |
| ------ | ------ |
| `bold` | Wrap in `**` |
| `italic` | Wrap in `*` |
| `strikethrough` | Wrap in `~~` |
| `heading` | Step the heading level down |
| `heading-smaller` | Step the heading level down |
| `heading-bigger` | Step the heading level up |
| `heading-1`, `heading-2`, `heading-3` | Set a fixed heading level |
| `code` | Fenced code block |
| `quote` | Blockquote |
| `unordered-list` | Bullet list |
| `ordered-list` | Numbered list |
| `check-list` | Task list |
| `clean-block` | Strip block formatting |
| `link` | Insert `[](https://)` |
| `image` | Insert `![](https://)` |
| `table` | Insert a three-column table skeleton |
| `horizontal-rule` | Insert `-----` |
| `undo`, `redo` | Walk the edit history |
| `preview` | Toggle the `preview` parameter |

`TOOLBAR_ACTIONS` and `DEFAULT_TOOLBAR` are importable if you want to build a
toolbar programmatically. An unknown action raises `ValueError` at assignment
time rather than silently disappearing.

## Preview

`preview=True` shows a live rendering beside the editor (or below it with
`preview_location="bottom"`). The rendering goes through Panel's own
`pn.pane.Markdown`, which means it uses markdown-it with the same extensions as
every other markdown surface in your app, so the preview and the final render
agree. The pane is exposed as `preview_pane` if you want to restyle it.

```python
MarkdownEditor(value="# Title", preview=True, height=400)
```

Add `"preview"` to the toolbar to let the user toggle it.

## Pasting and dropping files

Set an `upload_handler` and a file pasted or dropped into the editor is sent to
the server, stored by your own code and referenced in the document:

```python
from pathlib import Path

import panel as pn

from panel_mde import MarkdownEditor

MEDIA = Path("media")


def store(file):
    (MEDIA / file.name).write_bytes(file.data)
    return f"/media/{file.name}"


editor = MarkdownEditor(upload_handler=store, accepted_filetypes=["image/*", "video/*"])
pn.serve(editor, static_dirs={"media": str(MEDIA)})
```

The handler is called with an [`UploadedFile`](#panel_mde.UploadedFile) holding
the name, MIME type, size and bytes of the file, and it may be a coroutine
function if storing is slow. Whatever it returns decides what is inserted:

| Returned | Inserted |
| -------- | -------- |
| A URL for an `image/*` file | `![name](url)` |
| A URL for a `video/*` file | `<video src="url" controls></video>` |
| A URL for an `audio/*` file | `<audio src="url" controls></audio>` |
| A URL for anything else | `[name](url)` |
| A markdown or HTML snippet | The snippet, untouched |
| `None` | Nothing; the file is rejected |

A result counts as a snippet, rather than a URL, when it contains whitespace or
starts with `!`, `[` or `<`, so returning something like
`'<img src="/media/photo.png" width="300">'` gives you full control of the
markup. Media is inserted as HTML because markdown has no syntax for video or
audio; Panel's Markdown pane renders it, so the preview shows the player too.

`value` does not change until the handler returns. In the meantime the editor
marks the spot the file will land in, and that marker follows the text the user
keeps typing, so the insertion happens where the file was dropped rather than
wherever the caret has since moved.

`accepted_filetypes` restricts what may be uploaded, as MIME types
(`'image/png'`), MIME type wildcards (`'image/*'`) or extensions (`'.png'`);
anything else is rejected in the browser without being sent. `max_upload_size`
caps a single file at 10MB by default. Each file crosses the websocket in one
message, so raising the cap above the server's `--websocket-max-message-size`
(20MB by default) means raising both.

Rejections and exceptions are reported in place, on the marker, and an
exception in the handler is also logged by the server.

## Assets

Everything the editor needs, including the toolbar icons, ships inside the
package and is served by the Panel server itself. No stylesheet, script, icon
font or spell-check dictionary is fetched from a third-party CDN at runtime.
Toolbar icons are inline SVG that inherit `currentColor`, which also means they
render correctly inside the shadow root Panel gives every component, with no
document-level `@font-face` registration.

Spell checking uses the browser's own checker and can be turned off with
`spellcheck=False`.

## Sizing

Without an explicit `height` or `sizing_mode` the editor takes an intrinsic
height of roughly 240px and grows with its content. Give it a `height` or a
height-stretching `sizing_mode` and it fills that box and scrolls instead.

The editor re-measures itself whenever the component is laid out or resized, so
it also works when it is rendered detached and attached later, as happens
inside a dialog or an initially collapsed card.

## API

::: panel_mde.MarkdownEditor
    options:
        show_root_heading: false
        members: false

::: panel_mde.UploadedFile
