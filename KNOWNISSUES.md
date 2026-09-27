# Known issues

Observations gathered on 2026-09-27 while driving a live QGIS 3.34.14-Prizren
instance through this server during development of an unrelated QGIS plugin.
Not fixed here — this is a note for a follow-up session that will work on the
server itself.

## 1. A blocking QGIS modal dialog silently stalls every subsequent tool call

If QGIS pops up any modal dialog (a Python exception dialog, a blocking
`QMessageBox`, etc.), the server keeps accepting calls but each one hangs
until the client-side timeout (~120s) kicks in and the call is moved to the
background. The underlying QGIS-side action usually already succeeded once
the dialog is dismissed — the "timeout" is purely the request queueing behind
the blocked Qt event loop, not a real failure. There is no detection of, or
distinct error for, "a modal dialog is blocking QGIS right now" — from the
client it looks identical to a slow/hung call.

Reproduced twice in the same session: calls stalled for 120s+ with no error;
enumerating top-level windows (Win32 `EnumWindows`) found a leftover
`"Wystąpił błąd podczas wykonywania kodu Pythona"` dialog each time, and
closing it externally (`WM_CLOSE`) immediately unstuck the whole queue.

Possible directions: a watchdog that detects an open modal on the QGIS side
and reports it distinctly (instead of a silent timeout), and/or an option to
auto-dismiss known non-interactive dialog classes.

## 2. `reload_plugin` / `reloadPlugin` doesn't fully purge the plugin's submodules

`qgis.utils.reloadPlugin()` (used by the `reload_qgis_plugin` tool) calls
`loadPlugin()` again but does not clear already-imported submodules of the
plugin's package from `sys.modules`. For a plugin with submodules (anything
beyond a flat single-file plugin), this means edits to submodules are
silently not picked up on reload — the old bytecode keeps running with no
error or warning that the reload was incomplete.

Workaround used this session: before reloading, explicitly call
`qgis.utils.unloadPlugin(name)`, then delete every `sys.modules` entry equal
to or starting with `f"{name}."`, then `loadPlugin(name)` +
`startPlugin(name)`. This reliably picks up submodule changes; the plain
`reload_qgis_plugin` tool alone does not.

## 3. `reload_plugin` / `reloadPlugin` can report success on a load that actually failed

Separately, `qgis.utils.loadPlugin()` returns `False` on import failure (and
routes the exception through `showException(..., messagebar=True)`, so it
does *not* pop a blocking dialog — good), but if the plugin's package name
was previously left in a broken state in `sys.modules` by an unrelated bug
(e.g. a bad `sys.path` entry shadowing the plugin's own top-level module),
the `reload_qgis_plugin` MCP tool itself returned
`{"status": "success", "result": {"status": "reloaded", ...}}` even though
the plugin was not actually active afterward (`plugin_name not in
qgis.utils.plugins`). The tool's "success" only reflects that the reload
call ran without raising, not that the plugin ended up loaded and started.

## 4. `install_qgis_plugin_from_directory` fails outright on any locked file

This tool copies the whole plugin directory tree unconditionally. If the
target QGIS process has already imported a native extension (`.pyd`) bundled
in the plugin (e.g. a compiled dependency shipped in a `lib/` folder), that
file is locked by Windows and the whole copy aborts with `[WinError 5]
Odmowa dostępu` (access denied) on that one file — even when every other
file in the tree is a plain, unlocked `.py`/`.ui` source file that could have
been copied fine. There's no partial-copy / skip-locked-files fallback, so a
single stale locked native module blocks deploying any other change via this
tool; copying the changed files individually (bypassing this tool) was the
only workaround.

## 5. `export_map_view_to_image` used to render all project layers regardless of visibility (fixed)

Hit directly this session and worked around by driving a `QgsMapSettings` +
`QgsMapRendererParallelJob` render manually via `execute_arbitrary_python_code`
instead. Already fixed on `main` in `a0f6ac5` ("Fix: Render map export in the
canvas CRS and layer tree order"), which landed on the remote while this note
was being written — left here only as a record that the workaround is no
longer needed as of that commit.

## 6. A live-window screenshot approach (external, not part of this server) can show a valid raster as blank

Not a bug in this server, but worth recording since it looked like one at
first: capturing the QGIS main window from outside (Win32 `PrintWindow`) can
render vector layers correctly while showing a raster layer as completely
blank/white, even though the raster is valid and renders correctly via an
in-process `QgsMapRendererParallelJob`. If this server ever grows its own
screenshot tool, it should render off-screen via `QgsMapSettings` rather than
capturing the live window, to avoid this class of false negative.
