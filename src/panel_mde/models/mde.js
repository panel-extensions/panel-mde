import EasyMDE from "easymde"

// Inline SVG icons. EasyMDE renders a toolbar item's `icon` option as raw
// HTML (falling back to a Font Awesome <i> element when only `className` is
// given), so shipping paths here removes the icon font entirely -- and with
// it the CDN download and the shadow-DOM @font-face problem, since inline
// SVG inherits `currentColor` and needs no font registration at all.
const ATTRS = 'xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"'

function icon(body) {
  return `<svg ${ATTRS}>${body}</svg>`
}

function glyph(body, chars) {
  const text = chars.map(([x, y, size, char]) => `<text x="${x}" y="${y}" font-size="${size}" font-weight="600" fill="currentColor" stroke="none">${char}</text>`).join("")
  return `<svg ${ATTRS}>${body}${text}</svg>`
}

const H = "M4 5v14M12 5v14M4 12h8"

const ICONS = {
  "bold": icon('<path d="M8 5h5a3.5 3.5 0 0 1 0 7H8z"/><path d="M8 12h6a3.5 3.5 0 0 1 0 7H8z"/>'),
  "italic": icon('<path d="M11 5h6M7 19h6M14 5l-4 14"/>'),
  "strikethrough": icon('<path d="M5 12h14M16 7a4 2 0 0 0-4-2h-1a3.5 3.5 0 0 0 0 7h2a3.5 3.5 0 0 1 0 7h-1.5a4 2 0 0 1-4-2"/>'),
  "heading": icon('<path d="M6 5v14M18 5v14M6 12h12"/>'),
  "heading-smaller": icon(`<path d="${H}"/><path d="M16 11l2 2 2-2"/>`),
  "heading-bigger": icon(`<path d="${H}"/><path d="M16 13l2-2 2 2"/>`),
  "heading-1": glyph(`<path d="${H}"/>`, [[15.5, 19, 11, "1"]]),
  "heading-2": glyph(`<path d="${H}"/>`, [[15.5, 19, 11, "2"]]),
  "heading-3": glyph(`<path d="${H}"/>`, [[15.5, 19, 11, "3"]]),
  "code": icon('<path d="M8 8l-4 4 4 4M16 8l4 4-4 4"/>'),
  "quote": icon('<path d="M5 5v14M10 8h9M10 12h9M10 16h6"/>'),
  "unordered-list": icon('<path d="M9 6h11M9 12h11M9 18h11M4.5 6h.01M4.5 12h.01M4.5 18h.01"/>'),
  "ordered-list": glyph('<path d="M11 6h9M11 12h9M11 18h9"/>', [[3, 8, 8, "1"], [3, 14.5, 8, "2"], [3, 21, 8, "3"]]),
  "check-list": icon('<path d="M11 6h9M11 12h9M11 18h9M3.5 6l1.5 1.5L8 4.5M3.5 12l1.5 1.5L8 10.5M3.5 18l1.5 1.5L8 16.5"/>'),
  "clean-block": icon('<path d="M19 20H8.5l-4.2-4.3a1 1 0 0 1 0-1.4l10-10a1 1 0 0 1 1.4 0l5 5a1 1 0 0 1 0 1.4L11.5 20"/><path d="M18 13.3L11.7 7"/>'),
  "link": icon('<path d="M9 15l6-6M11 6l.5-.5a5 5 0 0 1 7 7l-.5.5M13 18l-.4.5a5 5 0 0 1-7.1-7.1l.5-.4"/>'),
  "image": icon('<path d="M4 4h16v16H4z"/><path d="M8.5 9.5h.01"/><path d="M4 16l4-4c.9-.9 2.1-.9 3 0l4 4"/><path d="M13 15l1.5-1.5c.9-.9 2.1-.9 3 0L20 16"/>'),
  "table": icon('<path d="M4 4h16v16H4z"/><path d="M4 10h16M4 15h16M10 4v16"/>'),
  "horizontal-rule": icon('<path d="M4 12h16"/><path d="M6 7h12M6 17h12" opacity="0.4"/>'),
  "undo": icon('<path d="M9 14l-4-4 4-4"/><path d="M5 10h11a4 4 0 0 1 0 8h-1"/>'),
  "redo": icon('<path d="M15 14l4-4-4-4"/><path d="M19 10H8a4 4 0 0 0 0 8h1"/>'),
  "preview": icon('<path d="M10 12a2 2 0 1 0 4 0a2 2 0 0 0-4 0"/><path d="M21 12c-2.4 4-5.4 6-9 6s-6.6-2-9-6c2.4-4 5.4-6 9-6s6.6 2 9 6"/>'),
}

// Every exposed toolbar action, mapped to the EasyMDE command that
// implements it. `preview` is ours: it toggles the `preview` parameter so the
// live rendering goes through Panel's markdown-it pane rather than the
// marked.js preview EasyMDE bundles, which renders subtly differently from
// every other markdown surface in a Panel app.
const ACTIONS = {
  "bold": {action: EasyMDE.toggleBold, title: "Bold"},
  "italic": {action: EasyMDE.toggleItalic, title: "Italic"},
  "strikethrough": {action: EasyMDE.toggleStrikethrough, title: "Strikethrough"},
  "heading": {action: EasyMDE.toggleHeadingSmaller, title: "Heading"},
  "heading-smaller": {action: EasyMDE.toggleHeadingSmaller, title: "Smaller heading"},
  "heading-bigger": {action: EasyMDE.toggleHeadingBigger, title: "Bigger heading"},
  "heading-1": {action: (mde) => set_heading(mde, 1), title: "Heading 1"},
  "heading-2": {action: (mde) => set_heading(mde, 2), title: "Heading 2"},
  "heading-3": {action: (mde) => set_heading(mde, 3), title: "Heading 3"},
  "code": {action: EasyMDE.toggleCodeBlock, title: "Code"},
  "quote": {action: EasyMDE.toggleBlockquote, title: "Quote"},
  "unordered-list": {action: EasyMDE.toggleUnorderedList, title: "Bullet list"},
  "ordered-list": {action: EasyMDE.toggleOrderedList, title: "Numbered list"},
  "check-list": {action: EasyMDE.toggleCheckList, title: "Task list"},
  "clean-block": {action: EasyMDE.cleanBlock, title: "Clear formatting"},
  "link": {action: EasyMDE.drawLink, title: "Insert link"},
  "image": {action: EasyMDE.drawImage, title: "Insert image"},
  "table": {action: EasyMDE.drawTable, title: "Insert table"},
  "horizontal-rule": {action: EasyMDE.drawHorizontalRule, title: "Insert horizontal rule"},
  "undo": {action: EasyMDE.undo, title: "Undo", noDisable: true},
  "redo": {action: EasyMDE.redo, title: "Redo", noDisable: true},
  "preview": {toggle: "preview", title: "Toggle preview", noDisable: true},
}

// EasyMDE only exposes toggleHeadingSmaller/Bigger as public commands, so the
// fixed-level buttons rewrite the leading ATX marker directly.
function set_heading(mde, level) {
  const cm = mde.codemirror
  const marker = "#".repeat(level)
  cm.operation(() => {
    for (const range of cm.listSelections()) {
      const from = Math.min(range.anchor.line, range.head.line)
      const to = Math.max(range.anchor.line, range.head.line)
      for (let line = from; line <= to; line++) {
        const text = cm.getLine(line)
        const stripped = text.replace(/^\s*#{1,6}\s*/, "")
        const next = text === `${marker} ${stripped}` ? stripped : `${marker} ${stripped}`
        cm.replaceRange(next, {line, ch: 0}, {line, ch: text.length}, "+pnmde")
      }
    }
  })
  cm.focus()
}

function build_toolbar(spec, model) {
  if (!Array.isArray(spec) || spec.length === 0) {
    return false
  }
  const items = []
  for (const name of spec) {
    if (name === "|" || name === "separator") {
      items.push("|")
      continue
    }
    const entry = ACTIONS[name]
    if (entry == null) {
      console.warn(`[panel-mde] Ignoring unknown toolbar action '${name}'.`)
      continue
    }
    items.push({
      name,
      title: entry.title,
      icon: ICONS[name],
      noDisable: entry.noDisable === true,
      action: entry.toggle == null ? entry.action : () => { model[entry.toggle] = !model[entry.toggle] },
    })
  }
  return items.length ? items : false
}

// Replace the document with `next` using the smallest edit that produces it,
// so CodeMirror moves the caret and selections the way it would for a normal
// edit and the undo history survives. A naive setValue() resets the document,
// which drops undo and yanks the caret to the start -- unacceptable when the
// application appends to `value` (e.g. an image reference from an upload)
// while the user is mid-sentence.
function apply_value(cm, next) {
  const prev = cm.getValue()
  if (prev === next) {
    return
  }
  let start = 0
  while (start < prev.length && start < next.length && prev[start] === next[start]) {
    start++
  }
  let end = 0
  while (end < prev.length - start && end < next.length - start && prev[prev.length - 1 - end] === next[next.length - 1 - end]) {
    end++
  }
  const from = start
  const to = prev.length - end
  const inserted = next.slice(start, next.length - end)
  const delta = inserted.length - (to - from)

  // Map a character offset in the old document onto the new one. Offsets
  // before the edit are untouched, offsets after it shift by the length
  // change, and an offset inside the replaced span collapses to its end.
  function remap(index) {
    if (index <= from) {
      return index
    }
    return index >= to ? index + delta : from + inserted.length
  }

  const selections = cm.listSelections().map((range) => [cm.indexFromPos(range.anchor), cm.indexFromPos(range.head)])
  const scroll = cm.getScrollInfo()
  cm.replaceRange(inserted, cm.posFromIndex(from), cm.posFromIndex(to), "+pnmde")
  // CodeMirror advances a caret that sits exactly at the insertion point,
  // which is precisely the caret an append lands on, so restore explicitly.
  cm.setSelections(
    selections.map(([anchor, head]) => ({anchor: cm.posFromIndex(remap(anchor)), head: cm.posFromIndex(remap(head))})),
    undefined,
    {scroll: false},
  )
  cm.scrollTo(scroll.left, scroll.top)
}

export function render({model, el, view}) {
  // `el` is the container Panel sizes from height/sizing_mode. It is a plain
  // block by default, so a tall document would overflow it instead of
  // scrolling; a flex column lets the editor shrink to the given height.
  el.style.display = "flex"
  el.style.flexDirection = "column"
  el.style.minHeight = "0"

  const root = document.createElement("div")
  root.className = "pnmde-root"

  const editor_wrap = document.createElement("div")
  editor_wrap.className = "pnmde-editor"

  const preview_wrap = document.createElement("div")
  preview_wrap.className = "pnmde-preview"

  root.append(editor_wrap, preview_wrap)

  // The editor needs an intrinsic height unless the layout gives it one,
  // otherwise CodeMirror collapses; when Panel does size the component, let
  // it shrink freely instead of fighting the fixed height.
  const sizing_mode = view.model.sizing_mode || ""
  if (view.model.height != null || sizing_mode.includes("height") || sizing_mode === "stretch_both" || sizing_mode === "scale_both") {
    root.style.setProperty("--pnmde-min-height", "0px")
  }

  let editor = null
  // Set while a Python -> editor write is being applied, so the resulting
  // CodeMirror change event does not echo the value straight back.
  let applying = false
  let autofocused = false

  function commit(final) {
    if (applying || editor == null) {
      return
    }
    const text = editor.value()
    if (model.value_input !== text) {
      model.value_input = text
    }
    if ((final || model.on_keyup) && model.value !== text) {
      model.value = text
    }
  }

  function create() {
    const textarea = document.createElement("textarea")
    editor_wrap.replaceChildren(textarea)

    editor = new EasyMDE({
      element: textarea,
      initialValue: model.value,
      // Icons ship inline as SVG (see ICONS); never fetch the icon font.
      autoDownloadFontAwesome: false,
      // EasyMDE's bundled checker downloads en_US.aff/.dic from jsdelivr at
      // runtime. Use the browser's own spell checker instead.
      spellChecker: false,
      nativeSpellcheck: model.spellcheck,
      // CodeMirror measures a detached element as zero-size; the autorefresh
      // addon re-measures once the element gains a box, which is what makes
      // the editor usable inside a dialog that attaches it after render.
      autoRefresh: true,
      toolbar: build_toolbar(model.toolbar, model),
      toolbarTips: true,
      status: model.status_bar ? ["lines", "words", "cursor"] : false,
      placeholder: model.placeholder,
      lineNumbers: model.line_numbers,
      lineWrapping: model.line_wrapping,
      tabSize: model.tab_size,
      indentWithTabs: model.indent_with_tabs,
      unorderedListStyle: model.unordered_list_style,
      autofocus: model.autofocus,
      minHeight: "0px",
      // Panel owns the layout; EasyMDE's own fullscreen and side-by-side
      // modes are position:fixed and escape the component's box.
      sideBySideFullscreen: false,
    })

    const cm = editor.codemirror
    cm.on("change", () => commit(false))
    cm.on("blur", () => commit(true))
    // Matches panel.widgets.TextEditor: Ctrl/Cmd+Enter commits `value`
    // without waiting for focus to leave the editor.
    cm.addKeyMap({"Ctrl-Enter": () => commit(true), "Cmd-Enter": () => commit(true)})
    sync_disabled()
    refresh()
  }

  function destroy() {
    if (editor == null) {
      return
    }
    editor.toTextArea()
    editor = null
    editor_wrap.replaceChildren()
  }

  function rebuild() {
    destroy()
    create()
  }

  function refresh() {
    if (editor == null) {
      return
    }
    requestAnimationFrame(() => {
      editor?.codemirror.refresh()
      // CodeMirror's own autofocus runs while the component is still detached,
      // where focus() is a no-op, so claim focus on the first real layout.
      if (model.autofocus && !autofocused && editor != null) {
        autofocused = true
        editor.codemirror.focus()
      }
    })
  }

  function sync_disabled() {
    if (editor == null) {
      return
    }
    editor.codemirror.setOption("readOnly", model.disabled)
    root.classList.toggle("pnmde-disabled", model.disabled)
  }

  function sync_preview() {
    root.classList.toggle("pnmde-has-preview", model.preview)
    root.classList.toggle("pnmde-preview-bottom", model.preview_location === "bottom")
    // Resolve the child even while the preview is hidden: get_child is what
    // registers `preview_pane` as an accessed child, and Panel only renders
    // child views it knows the ESM asked for.
    const child = model.get_child("preview_pane")
    if (child == null) {
      preview_wrap.replaceChildren()
    } else if (child.parentNode !== preview_wrap) {
      preview_wrap.replaceChildren(child)
    }
    refresh()
  }

  create()
  sync_preview()

  model.on("value", () => {
    if (editor == null || editor.value() === model.value) {
      return
    }
    applying = true
    try {
      apply_value(editor.codemirror, model.value)
    } finally {
      applying = false
    }
    if (model.value_input !== model.value) {
      model.value_input = model.value
    }
  })

  model.on("disabled", sync_disabled)
  // Watching a child parameter is what makes Panel build and render the new
  // child view around the callback, which the lazily created preview needs.
  model.on(["preview", "preview_location", "preview_pane"], sync_preview)
  model.on("spellcheck", () => editor?.codemirror.setOption("spellcheck", model.spellcheck))
  model.on("line_wrapping", () => { editor?.codemirror.setOption("lineWrapping", model.line_wrapping); refresh() })
  model.on("tab_size", () => {
    editor?.codemirror.setOption("tabSize", model.tab_size)
    editor?.codemirror.setOption("indentUnit", model.tab_size)
  })
  model.on("indent_with_tabs", () => editor?.codemirror.setOption("indentWithTabs", model.indent_with_tabs))
  model.on("unordered_list_style", () => { if (editor != null) { editor.options.unorderedListStyle = model.unordered_list_style } })

  // Options EasyMDE only reads while constructing its DOM.
  model.on(["toolbar", "status_bar", "line_numbers", "placeholder"], rebuild)

  model.on("after_render", refresh)
  model.on("after_layout", refresh)
  model.on("resize", refresh)
  model.on("remove", destroy)

  return root
}
