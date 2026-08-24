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

// EasyMDE calls its upload feature "image", but a paste or a drop can carry
// any file, so the wording is generalised. Only shown when the status bar is
// enabled; the marker in the document is what reports progress otherwise.
const UPLOAD_TEXTS = {
  sbInit: "Attach files by dragging and dropping or pasting from the clipboard.",
  sbOnDragEnter: "Drop the file to upload it.",
  sbOnDrop: "Uploading #images_names#...",
  sbOnUploaded: "Uploaded #image_name#",
}

// Match a File against `accepted_filetypes`: MIME types, MIME type wildcards
// or extensions. Mirrored in panel_mde.upload.accepts, which re-checks the
// file on arrival because a websocket message cannot be trusted.
function accepts(patterns, file) {
  if (!Array.isArray(patterns) || patterns.length === 0) {
    return true
  }
  const name = (file.name || "").toLowerCase()
  const mime = (file.type || "").toLowerCase()
  return patterns.some((raw) => {
    const pattern = String(raw).trim().toLowerCase()
    if (pattern === "") {
      return false
    } else if (pattern.startsWith(".")) {
      return name.endsWith(pattern)
    } else if (pattern.endsWith("/*")) {
      return mime.startsWith(pattern.slice(0, -1))
    }
    return mime === pattern
  })
}

function human_size(bytes) {
  const units = ["B", "KB", "MB", "GB"]
  let value = bytes
  let unit = 0
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024
    unit++
  }
  return `${unit === 0 || value >= 10 ? Math.round(value) : value.toFixed(1)}${units[unit]}`
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

  const splitter = document.createElement("div")
  splitter.className = "pnmde-splitter"
  splitter.setAttribute("role", "separator")
  splitter.setAttribute("tabindex", "0")
  splitter.setAttribute("aria-label", "Resize the preview")
  splitter.setAttribute("aria-valuemin", "10")
  splitter.setAttribute("aria-valuemax", "90")

  root.append(editor_wrap, splitter, preview_wrap)

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
  // Uploads waiting on a URL from the upload handler, by message id.
  const uploads = new Map()
  let upload_count = 0

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

  // EasyMDE's upload hook, called once per pasted or dropped file. Its
  // onSuccess is never used: what gets inserted depends on the type of the
  // file and is decided by the server, so the reply is handled below. onError
  // only drives EasyMDE's status bar, hence the marker in the document.
  async function upload(file, on_success, on_error) {
    const cm = editor?.codemirror
    if (cm == null) {
      return
    }
    const id = `u${++upload_count}`
    // A marker rather than placeholder text: `value` must not change until
    // the URL arrives, and a bookmark still tracks the insertion point
    // through everything the user types while the upload is in flight.
    const chip = document.createElement("span")
    chip.className = "pnmde-upload"
    chip.textContent = `Uploading ${file.name}...`
    // Text typed at a bookmark ends up to its right by default, which is what
    // keeps the file at the spot it was pasted rather than after whatever the
    // user typed while it uploaded.
    const bookmark = cm.setBookmark(cm.getCursor("to"), {widget: chip})
    uploads.set(id, {bookmark, chip, on_error, name: file.name, failed: false, message: "", timer: null})
    refresh_upload_status()

    const limit = model.max_upload_size
    if (!accepts(model.accepted_filetypes, file)) {
      fail_upload(id, `${file.name} is not an accepted file type.`)
      return
    } else if (limit != null && file.size > limit) {
      fail_upload(id, `${file.name} is larger than the ${human_size(limit)} upload limit.`)
      return
    }
    try {
      model.send_msg({kind: "upload", id, name: file.name, mime_type: file.type, data: await file.arrayBuffer()})
    } catch (e) {
      fail_upload(id, `${file.name} could not be read.`)
    }
  }

  // Drop a pending upload's marker and report where it ended up.
  function clear_upload(id) {
    const entry = uploads.get(id)
    uploads.delete(id)
    if (entry == null) {
      return null
    }
    if (entry.timer != null) {
      clearTimeout(entry.timer)
    }
    const pos = entry.bookmark.find()
    entry.bookmark.clear()
    refresh_upload_status()
    return pos
  }

  // EasyMDE writes "Uploading ..." into the status bar from its own paste and
  // drop handlers, but only clears it again from the onSuccess path, which is
  // never taken here, so the item is driven from this side instead. The write
  // is deferred: EasyMDE sets its own text after imageUploadFunction returns,
  // which is after a file rejected in the browser has already finished.
  function refresh_upload_status() {
    setTimeout(() => {
      if (editor == null) {
        return
      }
      const entries = [...uploads.values()]
      const pending = entries.filter((entry) => !entry.failed)
      const failed = entries.filter((entry) => entry.failed)
      let text = UPLOAD_TEXTS.sbInit
      if (pending.length) {
        text = UPLOAD_TEXTS.sbOnDrop.replace("#images_names#", pending.map((entry) => entry.name).join(", "))
      } else if (failed.length) {
        text = failed[failed.length - 1].message
      }
      editor.updateStatusBar("upload-image", text)
    }, 0)
  }

  function insert_upload(id, text) {
    const pos = clear_upload(id)
    const cm = editor?.codemirror
    if (cm == null || !text) {
      return
    }
    // A rebuilt editor has no marker left, so fall back to the caret.
    const at = pos || cm.getCursor()
    const focused = cm.hasFocus()
    cm.replaceRange(text, at, at, "+pnmde-upload")
    if (focused) {
      cm.setCursor(cm.posFromIndex(cm.indexFromPos(at) + text.length))
    }
  }

  function fail_upload(id, message) {
    const entry = uploads.get(id)
    if (entry == null) {
      return
    }
    // Keep the marker where the file was dropped, flipped to an error, so the
    // failure is reported at the place it happened rather than nowhere.
    entry.chip.classList.add("pnmde-upload-error")
    entry.chip.textContent = message
    entry.failed = true
    entry.message = message
    entry.timer = setTimeout(() => clear_upload(id), 8000)
    refresh_upload_status()
    entry.on_error(message)
  }

  function status_items() {
    if (!model.status_bar) {
      return false
    }
    // EasyMDE logs to the console whenever it updates a status item that does
    // not exist, and it updates 'upload-image' on every dragover event.
    const items = ["lines", "words", "cursor"]
    return model._upload_enabled ? ["upload-image", ...items] : items
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
      status: status_items(),
      // Registers the paste and drop handlers; they only exist when EasyMDE
      // is constructed with uploads enabled.
      uploadImage: model._upload_enabled,
      imageUploadFunction: upload,
      imageTexts: UPLOAD_TEXTS,
      // EasyMDE reports upload errors with alert() by default.
      errorCallback: (message) => console.warn(`[panel-mde] ${message}`),
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
    for (const id of [...uploads.keys()]) {
      clear_upload(id)
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

  // The editor takes `--pnmde-split` of the root and the preview takes the
  // rest. A fraction rather than pixels, so the ratio survives a resize.
  const MIN_SPLIT = 0.1
  let split = 0.5

  function set_split(fraction) {
    split = Math.min(1 - MIN_SPLIT, Math.max(MIN_SPLIT, fraction))
    root.style.setProperty("--pnmde-split", `${(split * 100).toFixed(3)}%`)
    splitter.setAttribute("aria-valuenow", `${Math.round(split * 100)}`)
    refresh()
  }

  function drag_split(event) {
    const bounds = root.getBoundingClientRect()
    const vertical = model.preview_location === "bottom"
    const size = vertical ? bounds.height : bounds.width
    if (size > 0) {
      set_split(((vertical ? event.clientY - bounds.top : event.clientX - bounds.left)) / size)
    }
  }

  splitter.addEventListener("pointerdown", (event) => {
    // Capture the pointer: without it CodeMirror and the preview swallow the
    // moves as soon as the cursor leaves the handle, which is immediately.
    splitter.setPointerCapture(event.pointerId)
    splitter.classList.add("pnmde-splitter-active")
    event.preventDefault()
  })
  splitter.addEventListener("pointermove", (event) => {
    if (splitter.hasPointerCapture(event.pointerId)) {
      drag_split(event)
    }
  })
  splitter.addEventListener("pointerup", (event) => {
    splitter.releasePointerCapture(event.pointerId)
    splitter.classList.remove("pnmde-splitter-active")
  })
  splitter.addEventListener("dblclick", () => set_split(0.5))
  splitter.addEventListener("keydown", (event) => {
    const step = {ArrowLeft: -0.02, ArrowUp: -0.02, ArrowRight: 0.02, ArrowDown: 0.02}[event.key]
    if (step != null) {
      event.preventDefault()
      set_split(split + step)
    }
  })

  function sync_preview() {
    root.classList.toggle("pnmde-has-preview", model.preview)
    root.classList.toggle("pnmde-preview-bottom", model.preview_location === "bottom")
    splitter.setAttribute("aria-orientation", model.preview_location === "bottom" ? "horizontal" : "vertical")
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

  set_split(split)
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

  model.on("msg:custom", (msg) => {
    if (msg == null) {
      return
    } else if (msg.kind === "uploaded") {
      insert_upload(msg.id, msg.text)
    } else if (msg.kind === "upload_failed") {
      fail_upload(msg.id, msg.message)
    }
  })

  // Options EasyMDE only reads while constructing its DOM.
  model.on(["toolbar", "status_bar", "line_numbers", "placeholder", "_upload_enabled"], rebuild)

  model.on("after_render", refresh)
  model.on("after_layout", refresh)
  model.on("resize", refresh)
  model.on("remove", destroy)

  return root
}
