"""The MarkdownEditor widget, wrapping EasyMDE."""

from __future__ import annotations

import typing as t
from functools import partial
from inspect import iscoroutinefunction

import param
from panel.io.state import state
from panel.pane.markup import Markdown
from panel.viewable import Child
from panel.widgets.base import WidgetBase

from .base import MODELS_PATH, MDEditorComponent
from .upload import (
    UploadedFile,
    accepts,
    format_upload,
    guess_mime_type,
)

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

    accepted_filetypes = param.List(default=[], item_type=str, doc="""
        The file types an `upload_handler` accepts, as MIME types
        (`'image/png'`), MIME type wildcards (`'image/*'`) or extensions
        (`'.png'`). An empty list accepts every file. Anything else is
        rejected in the browser, without being sent to the server.""")

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

    max_upload_size = param.Integer(default=10_000_000, bounds=(0, None), allow_None=True, doc="""
        The largest file, in bytes, that may be pasted or dropped into the
        editor. Each file is sent to the server in a single websocket message,
        so this has to stay below the server's `--websocket-max-message-size`
        (20MB by default). `None` disables the check.""")

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

    # allow_refs=False: Panel resolves a coroutine function assigned to a
    # parameter as a reference, i.e. calls it with no arguments and stores
    # what it returns, which is not what an async upload handler is.
    upload_handler = param.Callable(default=None, allow_refs=False, doc="""
        A callback invoked when a file is pasted or dropped into the editor.
        It is called with an `UploadedFile` holding the name, MIME type, size
        and bytes of the file, may be a coroutine function, and should store
        the file and return the URL it is served from. The URL is turned into
        an image reference, a `<video>`/`<audio>` tag or a link, depending on
        the type of the file; return a markdown or HTML snippet instead to
        control the insertion yourself, or `None` to reject the file. Nothing
        is inserted until the handler returns, and the insertion point follows
        the text the user types while it runs.""")

    value = param.String(default="", doc="""
        The markdown source. Updated on every keystroke unless `on_keyup` is
        disabled, in which case it updates when the editor loses focus.""")

    value_input = param.String(default="", doc="""
        The markdown source, updated on every keystroke. Identical to `value`
        while `on_keyup` is enabled.""")

    _upload_enabled = param.Boolean(default=False, doc="""
        Whether an `upload_handler` is set. EasyMDE only listens for pastes
        and drops when it is told to at construction time, so the frontend
        needs this as a parameter rather than deducing it per event.""")

    _esm = MODELS_PATH / "mde.js"

    # A callable cannot be serialized; mapping it to None keeps it off the
    # data model and out of every property update.
    _rename = {"upload_handler": None}

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

    @param.depends("upload_handler", watch=True, on_init=True)
    def _sync_upload_enabled(self):
        self._upload_enabled = self.upload_handler is not None

    @param.depends("value", watch=True)
    def _sync_value(self):
        self.value_input = self.value
        self._sync_preview()

    def _sync_preview(self):
        # Only feed the preview while it is visible; rendering markdown on
        # every keystroke for a hidden pane is pure overhead.
        if isinstance(self.preview_pane, Markdown):
            self.preview_pane.object = self.value if self.preview else ""

    def _handle_msg(self, data: t.Any) -> None:
        if not isinstance(data, dict) or data.get("kind") != "upload":
            return
        uid = str(data.get("id") or "")
        name = str(data.get("name") or "file")
        contents = bytes(data.get("data") or b"")
        file = UploadedFile(
            name=name,
            mime_type=guess_mime_type(name, str(data.get("mime_type") or "")),
            size=len(contents),
            data=contents,
        )
        handler = self.upload_handler
        # The browser applies both limits before sending, but the message
        # arrives over a websocket and nothing guarantees it came from our
        # frontend, so the handler only ever sees a file it asked for.
        if handler is None:
            self._upload_failed(uid, "No upload_handler is set.")
        elif self.max_upload_size is not None and file.size > self.max_upload_size:
            self._upload_failed(uid, f"{file.name} is larger than max_upload_size.")
        elif not accepts(self.accepted_filetypes, file):
            self._upload_failed(uid, f"{file.name} is not an accepted file type.")
        elif iscoroutinefunction(handler):
            state.execute(partial(self._call_handler_async, handler, uid, file))
        else:
            state.execute(partial(self._call_handler, handler, uid, file))

    def _call_handler(self, handler: t.Callable, uid: str, file: UploadedFile) -> None:
        try:
            self._upload_finished(uid, file, handler(file))
        except Exception:
            # Report to the editor before re-raising, so the pending upload
            # does not sit there spinning while the traceback is logged.
            self._upload_failed(uid, f"Uploading {file.name} failed.")
            raise

    async def _call_handler_async(self, handler: t.Callable, uid: str, file: UploadedFile) -> None:
        try:
            self._upload_finished(uid, file, await handler(file))
        except Exception:
            self._upload_failed(uid, f"Uploading {file.name} failed.")
            raise

    def _upload_finished(self, uid: str, file: UploadedFile, result: t.Any) -> None:
        if result is None:
            self._upload_failed(uid, f"{file.name} was rejected.")
            return
        if not isinstance(result, str):
            raise ValueError(
                "MarkdownEditor.upload_handler must return a URL, a markdown "
                f"snippet or None, not {type(result).__name__}."
            )
        self._send_msg({"kind": "uploaded", "id": uid, "text": format_upload(result, file)})

    def _upload_failed(self, uid: str, message: str) -> None:
        self._send_msg({"kind": "upload_failed", "id": uid, "message": message})

    def _process_param_change(self, params):
        # Resolve the True shorthand here so the frontend only ever receives
        # an explicit list of actions or False.
        if params.get("toolbar") is True:
            params["toolbar"] = list(DEFAULT_TOOLBAR)
        return super()._process_param_change(params)


__all__ = ["DEFAULT_TOOLBAR", "TOOLBAR_ACTIONS", "MarkdownEditor", "UploadedFile"]
