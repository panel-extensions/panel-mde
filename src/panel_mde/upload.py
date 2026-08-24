"""The payload handed to an upload handler, and the markdown it turns into."""

from __future__ import annotations

import mimetypes
import re
from dataclasses import dataclass
from html import escape

# A handler returns either a bare URL or a ready-made snippet. A URL is a
# single token, so anything holding whitespace or opening with markdown or
# HTML syntax is taken as a snippet and inserted as it is.
_SNIPPET_PREFIXES = ("!", "[", "<")

_MEDIA_TAGS = {"video": "video", "audio": "audio"}


@dataclass(frozen=True)
class UploadedFile:
    """A file pasted or dropped into a `MarkdownEditor`."""

    name: str
    """The file name reported by the browser."""

    mime_type: str
    """The MIME type reported by the browser, or one guessed from `name`."""

    size: int
    """The size of `data` in bytes."""

    data: bytes
    """The file contents."""

    @property
    def extension(self) -> str:
        """The lower-cased extension of `name`, including the leading dot."""
        head, dot, tail = self.name.rpartition(".")
        return f".{tail.lower()}" if dot and head else ""


def guess_mime_type(name: str, mime_type: str = "") -> str:
    """
    Return the MIME type of a file, falling back to the extension.

    Browsers report an empty type for files they do not recognise, which
    would leave the markdown formatting with nothing to dispatch on.
    """
    if mime_type:
        return mime_type
    return mimetypes.guess_type(name)[0] or "application/octet-stream"


def accepts(patterns: list[str], file: UploadedFile) -> bool:
    """
    Whether `file` matches any of the given file type patterns.

    Parameters
    ----------
    patterns: list[str]
        MIME types (`'image/png'`), MIME type wildcards (`'image/*'`) or
        extensions (`'.png'`). An empty list accepts every file.
    file: UploadedFile
        The file to test.
    """
    if not patterns:
        return True
    name, mime = file.name.lower(), file.mime_type.lower()
    for pattern in patterns:
        pattern = pattern.strip().lower()
        if not pattern:
            continue
        if pattern.startswith("."):
            if name.endswith(pattern):
                return True
        elif pattern.endswith("/*"):
            if mime.startswith(pattern[:-1]):
                return True
        elif mime == pattern:
            return True
    return False


def is_snippet(result: str) -> bool:
    """Whether an upload handler result is a snippet rather than a bare URL."""
    return result.startswith(_SNIPPET_PREFIXES) or bool(re.search(r"\s", result))


def format_upload(result: str, file: UploadedFile) -> str:
    """
    Return the markdown inserted into the document for a handler result.

    A snippet is passed through untouched. A bare URL is turned into an image
    reference, a media tag or a link, depending on the type of the file.

    Parameters
    ----------
    result: str
        The URL or snippet the upload handler returned.
    file: UploadedFile
        The file that was uploaded.
    """
    if not result or is_snippet(result):
        return result
    kind = file.mime_type.partition("/")[0].lower()
    if kind in _MEDIA_TAGS:
        # Markdown has no syntax for video or audio, and every markdown
        # renderer in a Panel app allows raw HTML.
        tag = _MEDIA_TAGS[kind]
        return f'<{tag} src="{escape(result, quote=True)}" controls></{tag}>'
    prefix = "!" if kind == "image" else ""
    return f"{prefix}[{_label(file.name)}]({_destination(result)})"


def _label(name: str) -> str:
    return re.sub(r"([\\\[\]])", r"\\\1", name)


def _destination(url: str) -> str:
    # A link destination may only contain parentheses when it is wrapped in
    # angle brackets.
    return f"<{url}>" if "(" in url or ")" in url else url


__all__ = ["UploadedFile", "accepts", "format_upload", "guess_mime_type", "is_snippet"]
