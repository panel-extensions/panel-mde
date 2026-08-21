"""The MarkdownEditor widget, wrapping EasyMDE."""

from __future__ import annotations

import typing as t

import param
from panel.pane.markup import Markdown
from panel.viewable import Child
from panel.widgets.base import WidgetBase

from .base import MODELS_PATH, MDEditorComponent

#: Every toolbar action ``MarkdownEditor`` understands, in the order EasyMDE
#: groups them. ``"|"`` inserts a separator.
TOOLBAR_ACTIONS: tuple[str, ...] = (
    "bold",
    "italic",
    "strikethrough",
    "heading",
    "heading-smaller",
    "heading-bigger",
    "heading-1",
    "heading-2",
    "heading-3",
    "code",
    "quote",
    "unordered-list",
    "ordered-list",
    "check-list",
    "clean-block",
    "link",
    "image",
    "table",
    "horizontal-rule",
    "undo",
    "redo",
    "preview",
)

#: The toolbar rendered when ``toolbar=True``.
DEFAULT_TOOLBAR: list[str] = [
    "bold", "italic", "heading", "|",
    "unordered-list", "ordered-list", "table", "|",
    "link", "image", "|",
    "undo", "redo",
]

_SEPARATORS = ("|", "separator")


class Toolbar(param.ClassSelector):
    """A toolbar specification: ``True``, ``False`` or a list of action names."""

    def __init__(self, default=True, **params):
        super().__init__(default=default, class_=(list, bool), **params)

    def _validate(self, val):
        super()._validate(val)
        if not isinstance(val, list):
            return
        unknown = [
            item for item in val
            if item not in TOOLBAR_ACTIONS and item not in _SEPARATORS
        ]
        if unknown:
            options = ", ".join(repr(a) for a in TOOLBAR_ACTIONS)
            raise ValueError(
                f"Toolbar parameter {self.name!r} received unknown action(s) "
                f"{unknown}. Valid actions are: {options} and '|' for a separator."
            )


class MarkdownEditor(MDEditorComponent, WidgetBase):
    """
    The `MarkdownEditor` is a rich text editor whose `value` is markdown source.

    Unlike `panel.widgets.TextEditor`, which is Quill-based and stores HTML,
    `MarkdownEditor` reads and writes markdown, so the editor, the rendered
    output and anything else consuming the text agree on one format. It wraps
    [EasyMDE](https://github.com/Ionaru/easy-markdown-editor), bundled into
    the package along with its stylesheet, and renders its toolbar icons as
    inline SVG -- no icon font, spell-check dictionary or other asset is
    fetched from a third-party CDN at runtime.

    Writing `value` from Python applies the smallest edit that produces the new
    text, so the caret, the selection, the scroll position and the undo history
    all survive a programmatic update.

    :Example:

    >>> MarkdownEditor(value="# markdown in, markdown out", preview=True)
    """

    autofocus = param.Boolean(default=False, doc="""
        Whether to focus the editor on initial render.""")

    disabled = param.Boolean(default=False, doc="""
        Whether the editor is read-only.""")

    indent_with_tabs = param.Boolean(default=False, doc="""
        Whether indentation inserts a tab character rather than spaces.""")

    line_numbers = param.Boolean(default=False, doc="""
        Whether to display line numbers in the gutter.""")

    line_wrapping = param.Boolean(default=True, doc="""
        Whether long lines wrap instead of scrolling horizontally.""")

    on_keyup = param.Boolean(default=True, doc="""
        Whether to update the value on every keystroke or only when the editor
        loses focus. `value_input` always updates on every keystroke.""")

    placeholder = param.String(default="", doc="""
        Placeholder text shown while the editor is empty.""")

    preview = param.Boolean(default=False, doc="""
        Whether to show a live preview beside the editor. The preview is
        rendered by Panel's own markdown-it based Markdown pane, so it matches
        every other markdown surface in the application. EasyMDE's marked.js
        preview is never used.""")

    preview_location = param.Selector(default="right", objects=["right", "bottom"], doc="""
        Where to place the live preview relative to the editor.""")

    preview_pane = Child(default=None, doc="""
        The pane rendering the live preview. Created on demand the first time
        `preview` is enabled; assign a `Markdown` pane to control how the
        preview is rendered.""")

    spellcheck = param.Boolean(default=True, doc="""
        Whether to enable the browser's native spell checker. EasyMDE's own
        spell checker is never enabled because it downloads dictionaries from
        a public CDN at runtime.""")

    status_bar = param.Boolean(default=False, doc="""
        Whether to show EasyMDE's status bar with line, word and cursor counts.""")

    tab_size = param.Integer(default=2, bounds=(1, None), doc="""
        Number of spaces a single indent level corresponds to.""")

    toolbar = Toolbar(default=True, doc="""
        The formatting toolbar. `True` renders the default toolbar, `False`
        hides it, and a list of action names renders exactly those actions.
        See `panel_mde.TOOLBAR_ACTIONS` for the available actions and use
        `'|'` to insert a separator.""")

    unordered_list_style = param.Selector(default="-", objects=["-", "*", "+"], doc="""
        The marker inserted by the bullet list action.""")

    value = param.String(default="", doc="""
        The markdown source. Updated on every keystroke unless `on_keyup` is
        disabled, in which case it updates when the editor loses focus.""")

    value_input = param.String(default="", doc="""
        The markdown source, updated on every keystroke. Identical to `value`
        while `on_keyup` is enabled.""")

    _esm = MODELS_PATH / "mde.js"

    def __init__(self, value: str | None = None, **params: t.Any):
        if value is not None:
            params["value"] = value
        if "value" in params and "value_input" not in params:
            params["value_input"] = params["value"]
        super().__init__(**params)

    @param.depends("preview", watch=True, on_init=True)
    def _setup_preview(self):
        if self.preview and self.preview_pane is None:
            self.preview_pane = Markdown(
                self.value, sizing_mode="stretch_both",
                margin=0, css_classes=["pnmde-preview-pane"],
            )
        self._sync_preview()

    @param.depends("value", watch=True)
    def _sync_value(self):
        self.value_input = self.value
        self._sync_preview()

    def _sync_preview(self):
        # Only feed the preview while it is visible; rendering markdown on
        # every keystroke for a hidden pane is pure overhead.
        if isinstance(self.preview_pane, Markdown):
            self.preview_pane.object = self.value if self.preview else ""

    def _process_param_change(self, params):
        # Resolve the True shorthand here so the frontend only ever receives
        # an explicit list of actions or False.
        if params.get("toolbar") is True:
            params["toolbar"] = list(DEFAULT_TOOLBAR)
        return super()._process_param_change(params)


__all__ = ["DEFAULT_TOOLBAR", "TOOLBAR_ACTIONS", "MarkdownEditor"]
