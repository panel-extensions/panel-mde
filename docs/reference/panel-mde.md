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
