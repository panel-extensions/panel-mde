import asyncio
import re

import pytest
from panel.pane import Markdown

from panel_mde import DEFAULT_TOOLBAR, TOOLBAR_ACTIONS, MarkdownEditor, UploadedFile
from panel_mde.base import EASYMDE_VERSION, MODELS_PATH
from panel_mde.upload import accepts, format_upload, guess_mime_type, is_snippet


def test_value_positional():
    editor = MarkdownEditor("# Title")

    assert editor.value == "# Title"
    assert editor.value_input == "# Title"


def test_value_default_empty():
    editor = MarkdownEditor()

    assert editor.value == ""
    assert editor.value_input == ""


def test_value_input_follows_value():
    editor = MarkdownEditor()
    editor.value = "some *markdown*"

    assert editor.value_input == "some *markdown*"


def test_explicit_value_input_preserved():
    editor = MarkdownEditor(value="a", value_input="b")

    assert editor.value == "a"
    assert editor.value_input == "b"


def test_is_widget():
    from panel.widgets.base import WidgetBase

    assert isinstance(MarkdownEditor(), WidgetBase)


def test_value_is_a_reactive_reference():
    editor = MarkdownEditor(value="# Title")
    pane = Markdown(editor)

    assert pane.object == "# Title"

    editor.value = "# Other"
    assert pane.object == "# Other"


class TestToolbar:

    def test_default_is_true(self):
        assert MarkdownEditor().toolbar is True

    def test_true_resolves_to_default_toolbar(self):
        editor = MarkdownEditor()
        props = editor._process_param_change({"toolbar": True})

        assert props["toolbar"] == DEFAULT_TOOLBAR

    def test_false_passes_through(self):
        editor = MarkdownEditor(toolbar=False)

        assert editor._process_param_change({"toolbar": False})["toolbar"] is False

    def test_custom_list(self):
        toolbar = ["bold", "italic", "|", "table"]
        editor = MarkdownEditor(toolbar=toolbar)

        assert editor._process_param_change({"toolbar": toolbar})["toolbar"] == toolbar

    def test_empty_list(self):
        assert MarkdownEditor(toolbar=[]).toolbar == []

    def test_all_documented_actions_accepted(self):
        MarkdownEditor(toolbar=list(TOOLBAR_ACTIONS))

    def test_unknown_action_rejected(self):
        with pytest.raises(ValueError, match=r"unknown action\(s\) \['bogus'\]"):
            MarkdownEditor(toolbar=["bold", "bogus"])

    def test_unknown_action_rejected_on_assignment(self):
        editor = MarkdownEditor()
        with pytest.raises(ValueError, match=r"unknown action\(s\)"):
            editor.toolbar = ["nope"]

    def test_default_toolbar_actions_are_valid(self):
        assert all(
            item in TOOLBAR_ACTIONS or item == "|" for item in DEFAULT_TOOLBAR
        )

    def test_table_is_available(self):
        assert "table" in TOOLBAR_ACTIONS
        assert "table" in DEFAULT_TOOLBAR


class TestPreview:

    def test_no_pane_until_enabled(self):
        assert MarkdownEditor(value="# Title").preview_pane is None

    def test_pane_created_on_enable(self):
        editor = MarkdownEditor(value="# Title")
        editor.preview = True

        assert isinstance(editor.preview_pane, Markdown)
        assert editor.preview_pane.object == "# Title"

    def test_pane_created_on_init(self):
        editor = MarkdownEditor(value="# Title", preview=True)

        assert isinstance(editor.preview_pane, Markdown)
        assert editor.preview_pane.object == "# Title"

    def test_pane_tracks_value(self):
        editor = MarkdownEditor(preview=True)
        editor.value = "updated"

        assert editor.preview_pane.object == "updated"

    def test_pane_not_fed_while_hidden(self):
        editor = MarkdownEditor(value="# Title", preview=True)
        editor.preview = False

        assert editor.preview_pane.object == ""

        editor.value = "ignored while hidden"
        assert editor.preview_pane.object == ""

    def test_pane_refilled_on_reenable(self):
        editor = MarkdownEditor(value="# Title", preview=True)
        editor.preview = False
        editor.value = "changed while hidden"
        editor.preview = True

        assert editor.preview_pane.object == "changed while hidden"

    def test_pane_is_a_child_of_the_model(self):
        editor = MarkdownEditor(value="# Title", preview=True)
        root = editor.get_root()

        assert root.children == ["preview_pane"]
        assert root.data.preview_pane is not None

    def test_preview_location(self):
        assert MarkdownEditor().preview_location == "right"
        assert MarkdownEditor(preview_location="bottom").preview_location == "bottom"

        with pytest.raises(ValueError):
            MarkdownEditor(preview_location="left")


def png(name="photo.png", data=b"\x89PNG"):
    return {"kind": "upload", "id": "u1", "name": name, "mime_type": "image/png", "data": data}


@pytest.fixture
def sent(monkeypatch):
    """Collects the messages an editor sends to the frontend."""
    messages = []
    monkeypatch.setattr(MarkdownEditor, "_send_msg", lambda self, data: messages.append(data))
    return messages


class TestUploadedFile:

    def test_extension(self):
        assert UploadedFile("photo.PNG", "image/png", 4, b"data").extension == ".png"
        assert UploadedFile("archive.tar.gz", "application/gzip", 4, b"data").extension == ".gz"
        assert UploadedFile("README", "text/plain", 4, b"data").extension == ""
        assert UploadedFile(".gitignore", "text/plain", 4, b"data").extension == ""

    def test_guess_mime_type(self):
        assert guess_mime_type("clip.mp4", "video/quicktime") == "video/quicktime"
        assert guess_mime_type("clip.mp4") == "video/mp4"
        assert guess_mime_type("mystery.zyx") == "application/octet-stream"


class TestFormatUpload:

    def test_image(self):
        file = UploadedFile("photo.png", "image/png", 4, b"data")

        assert format_upload("/media/photo.png", file) == "![photo.png](/media/photo.png)"

    def test_video(self):
        file = UploadedFile("clip.mp4", "video/mp4", 4, b"data")

        assert format_upload("/media/clip.mp4", file) == '<video src="/media/clip.mp4" controls></video>'

    def test_audio(self):
        file = UploadedFile("note.m4a", "audio/mp4", 4, b"data")

        assert format_upload("/media/note.m4a", file) == '<audio src="/media/note.m4a" controls></audio>'

    def test_other_types_become_a_link(self):
        file = UploadedFile("notes.pdf", "application/pdf", 4, b"data")

        assert format_upload("/media/notes.pdf", file) == "[notes.pdf](/media/notes.pdf)"

    def test_snippet_inserted_verbatim(self):
        file = UploadedFile("photo.png", "image/png", 4, b"data")

        for snippet in (
            "![alt](/media/photo.png)",
            "<img src='/media/photo.png' width='200'>",
            "[photo][ref]\n\n[ref]: /media/photo.png",
            "see /media/photo.png",
        ):
            assert format_upload(snippet, file) == snippet

    def test_url_with_parentheses_wrapped(self):
        file = UploadedFile("photo.png", "image/png", 4, b"data")

        assert format_upload("/media/photo(1).png", file) == "![photo.png](</media/photo(1).png>)"

    def test_brackets_in_name_escaped(self):
        file = UploadedFile("a[1].png", "image/png", 4, b"data")

        assert format_upload("/media/a.png", file) == r"![a\[1\].png](/media/a.png)"

    def test_media_url_escaped(self):
        file = UploadedFile("clip.mp4", "video/mp4", 4, b"data")

        assert format_upload('/media/"x".mp4', file) == '<video src="/media/&quot;x&quot;.mp4" controls></video>'

    def test_is_snippet(self):
        assert not is_snippet("https://example.com/a.png")
        assert is_snippet("![](a.png)")
        assert is_snippet("<video src='a.mp4'></video>")
        assert is_snippet("[a](b.png)")
        assert is_snippet("a b")


class TestAccepts:

    file = UploadedFile("photo.png", "image/png", 4, b"data")

    def test_empty_accepts_everything(self):
        assert accepts([], self.file)

    def test_mime_type(self):
        assert accepts(["image/png"], self.file)
        assert not accepts(["image/jpeg"], self.file)

    def test_wildcard(self):
        assert accepts(["image/*"], self.file)
        assert not accepts(["video/*"], self.file)

    def test_extension(self):
        assert accepts([".PNG"], self.file)
        assert not accepts([".jpg"], self.file)

    def test_any_pattern_matches(self):
        assert accepts([".mp4", "image/*"], self.file)


class TestUpload:

    def test_disabled_without_handler(self):
        assert MarkdownEditor()._upload_enabled is False

    def test_enabled_with_handler(self):
        editor = MarkdownEditor(upload_handler=lambda file: "/media/x.png")

        assert editor._upload_enabled is True

        editor.upload_handler = None
        assert editor._upload_enabled is False

    def test_handler_is_not_synced(self):
        editor = MarkdownEditor(upload_handler=lambda file: "/media/x.png")

        assert "upload_handler" not in editor._data_model.properties()
        assert "upload_handler" not in editor._process_param_change({"upload_handler": print})

    def test_handler_receives_the_file(self, sent):
        received = []
        editor = MarkdownEditor(upload_handler=lambda file: received.append(file) or "/media/photo.png")
        editor._handle_msg(png())

        assert len(received) == 1
        file = received[0]
        assert (file.name, file.mime_type, file.size, file.data) == ("photo.png", "image/png", 4, b"\x89PNG")
        assert sent == [{"kind": "uploaded", "id": "u1", "text": "![photo.png](/media/photo.png)"}]

    def test_mime_type_guessed_when_missing(self, sent):
        received = []
        editor = MarkdownEditor(upload_handler=lambda file: received.append(file) or "/media/clip.mp4")
        editor._handle_msg(dict(png(name="clip.mp4"), mime_type=""))

        assert received[0].mime_type == "video/mp4"
        assert sent[0]["text"] == '<video src="/media/clip.mp4" controls></video>'

    def test_snippet_result(self, sent):
        editor = MarkdownEditor(upload_handler=lambda file: f"![{file.name}](/x.png 'a title')")
        editor._handle_msg(png())

        assert sent[0]["text"] == "![photo.png](/x.png 'a title')"

    def test_none_rejects(self, sent):
        editor = MarkdownEditor(upload_handler=lambda file: None)
        editor._handle_msg(png())

        assert sent == [{"kind": "upload_failed", "id": "u1", "message": "photo.png was rejected."}]

    def test_no_handler_reports_failure(self, sent):
        MarkdownEditor()._handle_msg(png())

        assert sent == [{"kind": "upload_failed", "id": "u1", "message": "No upload_handler is set."}]

    def test_oversized_file_rejected_without_calling_the_handler(self, sent):
        called = []
        editor = MarkdownEditor(upload_handler=called.append, max_upload_size=2)
        editor._handle_msg(png())

        assert called == []
        assert sent[0]["message"] == "photo.png is larger than max_upload_size."

    def test_no_limit(self, sent):
        editor = MarkdownEditor(upload_handler=lambda file: "/media/photo.png", max_upload_size=None)
        editor._handle_msg(png())

        assert sent[0]["kind"] == "uploaded"

    def test_unaccepted_type_rejected_without_calling_the_handler(self, sent):
        called = []
        editor = MarkdownEditor(upload_handler=called.append, accepted_filetypes=["video/*"])
        editor._handle_msg(png())

        assert called == []
        assert sent[0]["message"] == "photo.png is not an accepted file type."

    def test_handler_exception_reports_failure(self, sent):
        def boom(file):
            raise RuntimeError("storage is down")

        editor = MarkdownEditor(upload_handler=boom)
        with pytest.raises(RuntimeError, match="storage is down"):
            editor._handle_msg(png())

        assert sent == [{"kind": "upload_failed", "id": "u1", "message": "Uploading photo.png failed."}]

    def test_non_string_result_reports_failure(self, sent):
        editor = MarkdownEditor(upload_handler=lambda file: 42)
        with pytest.raises(ValueError, match="must return a URL"):
            editor._handle_msg(png())

        assert sent[0]["kind"] == "upload_failed"

    def test_other_messages_ignored(self, sent):
        called = []
        editor = MarkdownEditor(upload_handler=called.append)
        editor._handle_msg({"kind": "something-else"})
        editor._handle_msg("nonsense")

        assert (called, sent) == ([], [])

    async def test_async_handler(self, sent):
        async def store(file):
            await asyncio.sleep(0)
            return f"/media/{file.name}"

        editor = MarkdownEditor(upload_handler=store)
        editor._handle_msg(png())
        for _ in range(5):
            await asyncio.sleep(0)

        assert sent == [{"kind": "uploaded", "id": "u1", "text": "![photo.png](/media/photo.png)"}]


class TestAssets:
    """The package must be self-contained and stay in sync with the pin."""

    def test_stylesheets_exist(self):
        for stylesheet in MarkdownEditor._stylesheets:
            assert stylesheet.is_file(), f"{stylesheet} is missing"

    def test_vendored_css_matches_pinned_version(self):
        css = (MODELS_PATH / "easymde.css").read_text(encoding="utf-8")
        match = re.search(r"^ \* easymde-version: (.+)$", css, re.MULTILINE)

        assert match is not None, "vendored stylesheet is missing its version header"
        assert match.group(1) == EASYMDE_VERSION, (
            "vendored stylesheet is stale; run `pixi run vendor-css`"
        )

    def test_vendored_css_has_no_external_references(self):
        css = (MODELS_PATH / "easymde.css").read_text(encoding="utf-8")

        assert "@font-face" not in css
        assert "url(" not in css

    def test_esm_pins_the_same_version(self):
        importmap = MarkdownEditor._importmap["imports"]

        assert importmap["easymde"].endswith(f"@{EASYMDE_VERSION}")

    def test_esm_disables_runtime_downloads(self):
        esm = MarkdownEditor._esm.read_text(encoding="utf-8")

        assert "autoDownloadFontAwesome: false" in esm
        assert "spellChecker: false" in esm
