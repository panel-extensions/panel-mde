import re

import pytest
from panel.pane import Markdown

from panel_mde import DEFAULT_TOOLBAR, TOOLBAR_ACTIONS, MarkdownEditor
from panel_mde.base import EASYMDE_VERSION, MODELS_PATH


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
