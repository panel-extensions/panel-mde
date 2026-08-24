import asyncio

import pytest

pytest.importorskip('playwright')

from panel.layout import Column
from panel.tests.util import serve_component, wait_until
from playwright.sync_api import expect

from panel_mde import DEFAULT_TOOLBAR, MarkdownEditor

pytestmark = pytest.mark.ui

# Hosts EasyMDE reaches for by default: the Font Awesome icon font and the
# spell-check dictionaries. Requirement: nothing is fetched from a
# third-party CDN at runtime.
FORBIDDEN_HOSTS = [
    'maxcdn.bootstrapcdn.com',
    'use.fontawesome.com',
    'cdnjs.cloudflare.com',
    'cdn.jsdelivr.net',
    'unpkg.com',
    'esm.sh',
    'fonts.googleapis.com',
    'fonts.gstatic.com',
]

EDITOR = '.pnmde-editor .CodeMirror'


def click_editor(page):
    """Focus the editor and return its locator."""
    editor = page.locator(EDITOR)
    editor.click()
    return editor


# CodeMirror forwards a DOM paste on its hidden textarea (and a drop on its
# scroller) to the handlers EasyMDE registers, which is what turns a file in
# the clipboard or in a drag into an upload.
DISPATCH_FILE = """
(el, {name, mime_type, size, event}) => {
  const transfer = new DataTransfer()
  transfer.items.add(new File([new Uint8Array(size)], name, {type: mime_type}))
  const init = {bubbles: true, cancelable: true}
  el.dispatchEvent(event === "paste"
    ? new ClipboardEvent("paste", {...init, clipboardData: transfer})
    : new DragEvent("drop", {...init, dataTransfer: transfer}))
}
"""


def paste_file(page, name="photo.png", mime_type="image/png", size=8):
    page.locator('.CodeMirror textarea').evaluate(
        DISPATCH_FILE, {"name": name, "mime_type": mime_type, "size": size, "event": "paste"}
    )


def drop_file(page, name="photo.png", mime_type="image/png", size=8):
    page.locator('.CodeMirror-scroll').evaluate(
        DISPATCH_FILE, {"name": name, "mime_type": mime_type, "size": size, "event": "drop"}
    )


def scroll_top(page):
    return page.locator('.CodeMirror-scroll').evaluate('el => el.scrollTop')


def first_rendered_line(page):
    return page.locator('.CodeMirror-code .CodeMirror-line').first.inner_text()


def test_renders_editor(page):
    editor = MarkdownEditor(value="# Title")
    serve_component(page, editor)

    expect(page.locator('.pnmde-root')).to_have_count(1)
    expect(page.locator('.EasyMDEContainer')).to_have_count(1)
    expect(page.locator(EDITOR)).to_have_count(1)
    expect(page.locator('.CodeMirror-code')).to_contain_text("# Title")


def test_stylesheets_reach_the_shadow_root(page):
    editor = MarkdownEditor(value="# Title")
    serve_component(page, editor)

    toolbar = page.locator('.editor-toolbar')
    # From the vendored easymde.css ...
    expect(toolbar).to_have_css('border-top-left-radius', '4px')
    # ... and from mde.css, which layers on top of it.
    expect(toolbar).to_have_css('padding', '2px 4px')
    expect(page.locator('.editor-toolbar button.bold')).to_have_css('width', '28px')


def test_toolbar_icons_are_inline_svg(page):
    editor = MarkdownEditor()
    serve_component(page, editor)

    actions = [item for item in DEFAULT_TOOLBAR if item != '|']
    expect(page.locator('.editor-toolbar button')).to_have_count(len(actions))
    for action in actions:
        expect(page.locator(f'.editor-toolbar button.{action} > svg')).to_have_count(1)

    # No Font Awesome <i> placeholders and no injected icon-font stylesheet.
    expect(page.locator('.editor-toolbar button > i')).to_have_count(0)
    expect(page.locator('link[href*="font-awesome"]')).to_have_count(0)


def test_no_third_party_requests(page):
    requested = []
    page.on('request', lambda request: requested.append(request.url))

    editor = MarkdownEditor(value="# Title", spellcheck=True)
    serve_component(page, editor)

    click_editor(page)
    page.keyboard.type("mispeled wrods")
    page.locator('.editor-toolbar button.bold').click()
    wait_until(lambda: "mispeled wrods" in editor.value, page)

    offenders = [url for url in requested if any(host in url for host in FORBIDDEN_HOSTS)]
    assert not offenders, f"requested third-party assets: {offenders}"


class TestValueSync:

    def test_value_syncs_per_keystroke(self, page):
        editor = MarkdownEditor()
        serve_component(page, editor)

        click_editor(page)
        page.keyboard.type("hello")

        wait_until(lambda: editor.value == "hello", page)
        wait_until(lambda: editor.value_input == "hello", page)

    def test_value_deferred_until_blur(self, page):
        editor = MarkdownEditor(on_keyup=False)
        serve_component(page, editor)

        click_editor(page)
        page.keyboard.type("hello")

        wait_until(lambda: editor.value_input == "hello", page)
        assert editor.value == ""

        page.locator('.editor-toolbar button.bold').click()  # steals focus, blurring the editor
        wait_until(lambda: editor.value.startswith("hello"), page)

    def test_ctrl_enter_commits(self, page):
        editor = MarkdownEditor(on_keyup=False)
        serve_component(page, editor)

        click_editor(page)
        page.keyboard.type("hello")
        wait_until(lambda: editor.value_input == "hello", page)

        page.keyboard.press("Control+Enter")
        wait_until(lambda: editor.value == "hello", page)

    def test_programmatic_write_renders(self, page):
        editor = MarkdownEditor()
        serve_component(page, editor)

        editor.value = "# From Python"
        expect(page.locator('.CodeMirror-code')).to_contain_text("# From Python")
        wait_until(lambda: editor.value_input == "# From Python", page)

    def test_programmatic_write_does_not_echo(self, page):
        editor = MarkdownEditor()
        serve_component(page, editor)
        changes = []
        editor.param.watch(lambda e: changes.append(e.new), 'value')

        editor.value = "# From Python"
        expect(page.locator('.CodeMirror-code')).to_contain_text("# From Python")
        page.wait_for_timeout(300)

        assert changes == ["# From Python"]


class TestCaretPreservation:
    """Requirement: a programmatic ``value`` write must not disturb the user."""

    def test_caret_preserved(self, page):
        editor = MarkdownEditor(value="hello world")
        serve_component(page, editor)

        click_editor(page)
        page.keyboard.press("Home")
        for _ in range(5):
            page.keyboard.press("ArrowRight")

        # An upload flow appending an image reference while the user is mid-word.
        editor.value = "hello world\n\n![shot](shot.png)"
        expect(page.locator('.CodeMirror-code')).to_contain_text("![shot](shot.png)")

        page.keyboard.type("!")
        wait_until(lambda: editor.value == "hello! world\n\n![shot](shot.png)", page)

    def test_caret_preserved_at_the_append_point(self, page):
        editor = MarkdownEditor(value="hello")
        serve_component(page, editor)

        click_editor(page)
        page.keyboard.press("End")

        # The caret sits exactly where the new text is inserted; CodeMirror
        # would carry it along to the end of the insertion.
        editor.value = "hello\n\n![shot](shot.png)"
        expect(page.locator('.CodeMirror-code')).to_contain_text("![shot](shot.png)")

        page.keyboard.type("!")
        wait_until(lambda: editor.value == "hello!\n\n![shot](shot.png)", page)

    def test_selection_preserved(self, page):
        editor = MarkdownEditor(value="hello world")
        serve_component(page, editor)

        click_editor(page)
        page.keyboard.press("Home")
        for _ in range(5):
            page.keyboard.press("Shift+ArrowRight")

        editor.value = "hello world\n\nappended"
        expect(page.locator('.CodeMirror-code')).to_contain_text("appended")

        # The selection still covers "hello", so bold wraps just that word.
        page.locator('.editor-toolbar button.bold').click()
        wait_until(lambda: editor.value == "**hello** world\n\nappended", page)

    def test_scroll_preserved(self, page):
        body = "\n".join(f"line {i}" for i in range(200))
        editor = MarkdownEditor(value=body, height=240)
        serve_component(page, editor)

        page.locator('.CodeMirror-scroll').hover()
        page.mouse.wheel(0, 600)
        wait_until(lambda: scroll_top(page) > 100, page)
        before = scroll_top(page)
        first = first_rendered_line(page)

        # CodeMirror only renders the visible viewport, so the prepended line
        # never enters the DOM; the shift of the first rendered line is what
        # tells us Python's write landed.
        editor.value = f"PREPENDED\n{body}"
        wait_until(lambda: first_rendered_line(page) != first, page)

        assert abs(scroll_top(page) - before) <= 2

    def test_undo_survives_programmatic_write(self, page):
        editor = MarkdownEditor()
        serve_component(page, editor)

        click_editor(page)
        page.keyboard.type("typed by hand")
        wait_until(lambda: editor.value == "typed by hand", page)

        editor.value = "typed by hand\n\nappended"
        expect(page.locator('.CodeMirror-code')).to_contain_text("appended")

        # A setValue() would have wiped the history, leaving undo a no-op.
        page.locator('.editor-toolbar button.undo').click()
        wait_until(lambda: editor.value == "typed by hand", page)


class TestToolbar:

    def test_bold(self, page):
        editor = MarkdownEditor()
        serve_component(page, editor)

        click_editor(page)
        page.keyboard.type("hello")
        page.keyboard.press("Shift+Home")
        page.locator('.editor-toolbar button.bold').click()

        wait_until(lambda: editor.value == "**hello**", page)

    def test_italic(self, page):
        editor = MarkdownEditor()
        serve_component(page, editor)

        click_editor(page)
        page.keyboard.type("hello")
        page.keyboard.press("Shift+Home")
        page.locator('.editor-toolbar button.italic').click()

        wait_until(lambda: editor.value == "*hello*", page)

    def test_heading(self, page):
        editor = MarkdownEditor(value="Title")
        serve_component(page, editor)

        click_editor(page)
        page.locator('.editor-toolbar button.heading').click()

        wait_until(lambda: editor.value == "# Title", page)

    def test_heading_levels(self, page):
        editor = MarkdownEditor(value="Title", toolbar=["heading-1", "heading-2", "heading-3"])
        serve_component(page, editor)

        click_editor(page)
        page.locator('.editor-toolbar button.heading-2').click()
        wait_until(lambda: editor.value == "## Title", page)

        page.locator('.editor-toolbar button.heading-3').click()
        wait_until(lambda: editor.value == "### Title", page)

        # Clicking the active level again clears it.
        page.locator('.editor-toolbar button.heading-3').click()
        wait_until(lambda: editor.value == "Title", page)

    def test_unordered_list(self, page):
        editor = MarkdownEditor(value="item")
        serve_component(page, editor)

        click_editor(page)
        page.locator('.editor-toolbar button.unordered-list').click()

        wait_until(lambda: editor.value == "- item", page)

    def test_ordered_list(self, page):
        editor = MarkdownEditor(value="item")
        serve_component(page, editor)

        click_editor(page)
        page.locator('.editor-toolbar button.ordered-list').click()

        wait_until(lambda: editor.value == "1. item", page)

    def test_link(self, page):
        editor = MarkdownEditor()
        serve_component(page, editor)

        click_editor(page)
        page.locator('.editor-toolbar button.link').click()

        wait_until(lambda: editor.value == "[](https://)", page)

    def test_image(self, page):
        editor = MarkdownEditor()
        serve_component(page, editor)

        click_editor(page)
        page.locator('.editor-toolbar button.image').click()

        wait_until(lambda: editor.value == "![](https://)", page)

    def test_table(self, page):
        editor = MarkdownEditor()
        serve_component(page, editor)

        click_editor(page)
        page.locator('.editor-toolbar button.table').click()

        wait_until(lambda: "| Column 1 | Column 2 | Column 3 |" in editor.value, page)
        wait_until(lambda: "| -------- | -------- | -------- |" in editor.value, page)

    def test_undo_redo(self, page):
        editor = MarkdownEditor()
        serve_component(page, editor)

        click_editor(page)
        page.keyboard.type("hello")
        wait_until(lambda: editor.value == "hello", page)

        page.locator('.editor-toolbar button.undo').click()
        wait_until(lambda: editor.value == "", page)

        page.locator('.editor-toolbar button.redo').click()
        wait_until(lambda: editor.value == "hello", page)

    def test_toolbar_disabled(self, page):
        editor = MarkdownEditor(toolbar=False)
        serve_component(page, editor)

        expect(page.locator(EDITOR)).to_have_count(1)
        expect(page.locator('.editor-toolbar')).to_have_count(0)

    def test_custom_toolbar_order(self, page):
        editor = MarkdownEditor(toolbar=["table", "|", "bold"])
        serve_component(page, editor)

        expect(page.locator('.editor-toolbar button')).to_have_count(2)
        expect(page.locator('.editor-toolbar button').first).to_have_class('table')
        expect(page.locator('.editor-toolbar button').last).to_have_class('bold')
        expect(page.locator('.editor-toolbar i.separator')).to_have_count(1)

    def test_toolbar_rebuild_keeps_value(self, page):
        editor = MarkdownEditor(toolbar=["bold"])
        serve_component(page, editor)

        click_editor(page)
        page.keyboard.type("hello")
        wait_until(lambda: editor.value == "hello", page)

        editor.toolbar = ["bold", "italic", "table"]
        expect(page.locator('.editor-toolbar button')).to_have_count(3)
        expect(page.locator('.CodeMirror-code')).to_contain_text("hello")
        assert editor.value == "hello"


class TestPreview:

    def test_hidden_by_default(self, page):
        editor = MarkdownEditor(value="# Title")
        serve_component(page, editor)

        expect(page.locator('.pnmde-preview')).to_be_hidden()
        expect(page.locator('.pnmde-root')).not_to_have_class('pnmde-root pnmde-has-preview')

    def test_renders_with_panel_markdown(self, page):
        editor = MarkdownEditor(value="# Title", preview=True, height=300)
        serve_component(page, editor)

        expect(page.locator('.pnmde-preview')).to_be_visible()
        expect(page.locator('.pnmde-preview h1')).to_contain_text("Title")

    def test_tracks_typing(self, page):
        editor = MarkdownEditor(preview=True, height=300)
        serve_component(page, editor)

        click_editor(page)
        page.keyboard.type("## Live")

        expect(page.locator('.pnmde-preview h2')).to_contain_text("Live")

    def test_renders_tables(self, page):
        editor = MarkdownEditor(preview=True, height=300)
        serve_component(page, editor)

        click_editor(page)
        page.locator('.editor-toolbar button.table').click()

        expect(page.locator('.pnmde-preview table')).to_have_count(1)
        expect(page.locator('.pnmde-preview th').first).to_contain_text("Column 1")

    def test_toggled_after_render(self, page):
        editor = MarkdownEditor(value="# Title", height=300)
        serve_component(page, editor)

        expect(page.locator('.pnmde-preview')).to_be_hidden()

        editor.preview = True
        expect(page.locator('.pnmde-preview')).to_be_visible()
        expect(page.locator('.pnmde-preview h1')).to_contain_text("Title")

        editor.preview = False
        expect(page.locator('.pnmde-preview')).to_be_hidden()

    def test_toolbar_button_toggles(self, page):
        editor = MarkdownEditor(value="# Title", toolbar=["preview"], height=300)
        serve_component(page, editor)

        page.locator('.editor-toolbar button.preview').click()
        wait_until(lambda: editor.preview, page)
        expect(page.locator('.pnmde-preview h1')).to_contain_text("Title")

        page.locator('.editor-toolbar button.preview').click()
        wait_until(lambda: not editor.preview, page)

    def test_bottom_location(self, page):
        editor = MarkdownEditor(value="# Title", preview=True, preview_location="bottom", height=400)
        serve_component(page, editor)

        expect(page.locator('.pnmde-root')).to_have_css('flex-direction', 'column')

        editor_box = page.locator('.pnmde-editor').bounding_box()
        preview_box = page.locator('.pnmde-preview').bounding_box()
        assert preview_box['y'] > editor_box['y']

    def test_split_stays_even_with_long_lines(self, page):
        editor = MarkdownEditor(
            value="word " * 400 + "https://example.com/" + "a" * 300,
            preview=True, width=800, height=300,
        )
        serve_component(page, editor)

        expect(page.locator('.pnmde-preview')).to_be_visible()
        editor_box = page.locator('.pnmde-editor').bounding_box()
        preview_box = page.locator('.pnmde-preview').bounding_box()
        assert abs(editor_box['width'] - preview_box['width']) < 2

    def test_splitter_drags(self, page):
        editor = MarkdownEditor(value="# Title", preview=True, width=800, height=300)
        serve_component(page, editor)

        splitter = page.locator('.pnmde-splitter')
        expect(splitter).to_be_visible()
        handle = splitter.bounding_box()
        start = page.locator('.pnmde-editor').bounding_box()['width']

        centre = (handle['x'] + handle['width'] / 2, handle['y'] + handle['height'] / 2)
        page.mouse.move(*centre)
        page.mouse.down()
        page.mouse.move(centre[0] - 200, centre[1], steps=5)
        page.mouse.up()

        width = page.locator('.pnmde-editor').bounding_box()['width']
        assert abs(width - (start - 200)) < 2, (start, width)
        assert page.locator('.pnmde-preview').bounding_box()['width'] > start

        # Double-clicking the handle puts it back in the middle.
        splitter.dblclick()
        wait_until(lambda: abs(page.locator('.pnmde-editor').bounding_box()['width'] - start) < 2, page)

    def test_splitter_hidden_without_a_preview(self, page):
        editor = MarkdownEditor(value="# Title", height=300)
        serve_component(page, editor)

        expect(page.locator('.pnmde-splitter')).to_be_hidden()


class TestOptions:

    def test_placeholder(self, page):
        editor = MarkdownEditor(placeholder="Write something")
        serve_component(page, editor)

        expect(page.locator('.CodeMirror-placeholder')).to_have_text("Write something")

    def test_disabled(self, page):
        editor = MarkdownEditor(value="frozen", disabled=True)
        serve_component(page, editor)

        expect(page.locator('.pnmde-root')).to_have_class('pnmde-root pnmde-disabled')

        click_editor(page)
        page.keyboard.type("nope")
        page.wait_for_timeout(300)
        assert editor.value == "frozen"

    def test_enabled_after_disabled(self, page):
        editor = MarkdownEditor(value="frozen", disabled=True)
        serve_component(page, editor)

        editor.disabled = False
        expect(page.locator('.pnmde-root')).not_to_have_class('pnmde-root pnmde-disabled')

        click_editor(page)
        page.keyboard.press("End")
        page.keyboard.type("!")
        wait_until(lambda: editor.value == "frozen!", page)

    def test_line_numbers(self, page):
        editor = MarkdownEditor(value="a\nb\nc")
        serve_component(page, editor)

        expect(page.locator('.CodeMirror-gutter.CodeMirror-linenumbers')).to_have_count(0)

        editor.line_numbers = True
        expect(page.locator('.CodeMirror-gutter.CodeMirror-linenumbers')).to_have_count(1)
        # CodeMirror keeps a spare number element around to measure the gutter,
        # so check the numbers that are there rather than how many.
        numbers = page.locator('.CodeMirror-linenumber')
        wait_until(lambda: {"1", "2", "3"} <= set(numbers.all_inner_texts()), page)

    def test_status_bar(self, page):
        editor = MarkdownEditor(value="a b c")
        serve_component(page, editor)

        expect(page.locator('.editor-statusbar')).to_have_count(0)

        editor.status_bar = True
        expect(page.locator('.editor-statusbar')).to_have_count(1)
        expect(page.locator('.editor-statusbar .words')).to_contain_text("3")

    def test_spellcheck(self, page):
        editor = MarkdownEditor(spellcheck=False)
        serve_component(page, editor)

        expect(page.locator('.CodeMirror textarea')).to_have_attribute('spellcheck', 'false')

    def test_autofocus(self, page):
        editor = MarkdownEditor(autofocus=True)
        serve_component(page, editor)

        expect(page.locator('.CodeMirror')).to_have_class('CodeMirror cm-s-easymde CodeMirror-wrap CodeMirror-focused')

    def test_unordered_list_style(self, page):
        editor = MarkdownEditor(value="item", unordered_list_style="*")
        serve_component(page, editor)

        click_editor(page)
        page.locator('.editor-toolbar button.unordered-list').click()

        wait_until(lambda: editor.value == "* item", page)


class TestUpload:
    """Pasting and dropping files, handled by ``upload_handler``."""

    def test_paste_inserts_an_image(self, page):
        received = []
        editor = MarkdownEditor(value="Before: ", upload_handler=lambda file: received.append(file) or f"/media/{file.name}")
        serve_component(page, editor)

        click_editor(page)
        page.keyboard.press("End")
        paste_file(page)

        wait_until(lambda: editor.value == "Before: ![photo.png](/media/photo.png)", page)
        assert len(received) == 1
        assert (received[0].name, received[0].mime_type, received[0].data) == ("photo.png", "image/png", b"\x00" * 8)

    def test_drop_inserts_a_video_tag(self, page):
        editor = MarkdownEditor(upload_handler=lambda file: f"/media/{file.name}")
        serve_component(page, editor)

        drop_file(page, name="clip.mp4", mime_type="video/mp4")

        wait_until(lambda: editor.value == '<video src="/media/clip.mp4" controls></video>', page)

    def test_snippet_inserted_verbatim(self, page):
        editor = MarkdownEditor(upload_handler=lambda file: f'<img src="/media/{file.name}" width="200">')
        serve_component(page, editor)

        paste_file(page)

        wait_until(lambda: editor.value == '<img src="/media/photo.png" width="200">', page)

    def test_nothing_happens_without_a_handler(self, page):
        editor = MarkdownEditor(value="untouched")
        serve_component(page, editor)

        paste_file(page)
        page.wait_for_timeout(400)

        assert editor.value == "untouched"
        expect(page.locator('.pnmde-upload')).to_have_count(0)

    def test_handler_attached_after_render(self, page):
        editor = MarkdownEditor()
        serve_component(page, editor)

        editor.upload_handler = lambda file: f"/media/{file.name}"
        # EasyMDE only listens for pastes when it is built with uploads on, so
        # the editor is rebuilt; wait for the new instance before pasting.
        page.wait_for_timeout(200)
        paste_file(page)

        wait_until(lambda: editor.value == "![photo.png](/media/photo.png)", page)

    def test_rejected_file_type_never_reaches_the_handler(self, page):
        called = []
        editor = MarkdownEditor(upload_handler=called.append, accepted_filetypes=["image/*"])
        serve_component(page, editor)

        paste_file(page, name="clip.mp4", mime_type="video/mp4")

        expect(page.locator('.pnmde-upload-error')).to_contain_text("clip.mp4 is not an accepted file type")
        assert called == []
        assert editor.value == ""

    def test_oversized_file_never_reaches_the_handler(self, page):
        called = []
        editor = MarkdownEditor(upload_handler=called.append, max_upload_size=4)
        serve_component(page, editor)

        paste_file(page, size=8)

        expect(page.locator('.pnmde-upload-error')).to_contain_text("photo.png is larger than")
        assert called == []
        assert editor.value == ""

    def test_rejection_by_the_handler_is_reported(self, page):
        editor = MarkdownEditor(upload_handler=lambda file: None)
        serve_component(page, editor)

        paste_file(page)

        expect(page.locator('.pnmde-upload-error')).to_contain_text("photo.png was rejected")
        assert editor.value == ""

    def test_marker_holds_the_spot_while_the_handler_runs(self, page):
        async def store(file):
            await asyncio.sleep(0.5)
            return f"/media/{file.name}"

        editor = MarkdownEditor(value="A", upload_handler=store)
        serve_component(page, editor)

        click_editor(page)
        page.keyboard.press("End")
        paste_file(page)

        # The document is untouched until the URL arrives; the marker is a
        # CodeMirror widget, so it shows up in the DOM but not in `value`.
        expect(page.locator('.pnmde-upload')).to_contain_text("Uploading photo.png")
        assert editor.value == "A"

        page.keyboard.type("BC")
        wait_until(lambda: editor.value == "A![photo.png](/media/photo.png)BC", page)
        expect(page.locator('.pnmde-upload')).to_have_count(0)

    def test_status_bar_reports_uploads(self, page):
        async def store(file):
            await asyncio.sleep(0.5)
            return f"/media/{file.name}"

        editor = MarkdownEditor(status_bar=True, upload_handler=store)
        serve_component(page, editor)

        status = page.locator('.editor-statusbar .upload-image')
        expect(status).to_contain_text("Attach files")

        paste_file(page)
        expect(status).to_contain_text("Uploading photo.png")

        wait_until(lambda: editor.value == "![photo.png](/media/photo.png)", page)
        # EasyMDE only clears its own "Uploading..." text from the code path
        # that inserts the image for us, which is never taken.
        expect(status).to_contain_text("Attach files")

    def test_status_bar_reports_a_rejected_file(self, page):
        editor = MarkdownEditor(status_bar=True, upload_handler=lambda file: None, max_upload_size=4)
        serve_component(page, editor)

        paste_file(page, size=8)

        expect(page.locator('.editor-statusbar .upload-image')).to_contain_text(
            "photo.png is larger than"
        )


def test_usable_when_attached_after_render(page):
    """CodeMirror measures a detached element as zero-size (dialogs, tabs)."""
    editor = MarkdownEditor(value="# Title", height=240)
    layout = Column(editor, visible=False)
    serve_component(page, layout)

    expect(page.locator('.pnmde-root')).to_be_hidden()

    layout.visible = True
    expect(page.locator(EDITOR)).to_be_visible()

    # A zero-measured editor leaves the sizer collapsed and swallows clicks.
    wait_until(lambda: page.locator('.CodeMirror-sizer').bounding_box()['height'] > 0, page)

    click_editor(page)
    page.keyboard.press("End")
    page.keyboard.type("!")
    wait_until(lambda: editor.value == "# Title!", page)
