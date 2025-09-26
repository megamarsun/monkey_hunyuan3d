# -*- coding: utf-8 -*-
"""Operators related to Blender Text datablocks for prompt management."""

from __future__ import annotations

import bpy
from bpy.app.translations import pgettext_iface as _
from bpy.props import StringProperty
from bpy.types import Operator

from . import get_logger

logger = get_logger()


def _get_settings(context: bpy.types.Context):
    scene = getattr(context, "scene", None)
    if scene is None:
        return None
    return getattr(scene, "mh3d_settings", None)


def _get_selected_text(settings) -> bpy.types.Text | None:
    if settings is None:
        return None
    text_name = getattr(settings, "prompt_text_name", "") or ""
    if not text_name:
        return None
    return bpy.data.texts.get(text_name)


class MH3D_OT_OpenTextEditor(Operator):
    bl_idname = "mh3d.open_text_editor"
    bl_label = _("Open Text Editor")
    bl_description = _("Open a separate Text Editor window for prompt editing.")

    def execute(self, context: bpy.types.Context) -> set[str]:
        window_manager = getattr(context, "window_manager", None)
        if window_manager is None:
            self.report({'ERROR'}, _("Settings unavailable."))
            logger.error("Window manager unavailable when opening Text Editor window.")
            return {'CANCELLED'}

        windows_before = {window.as_pointer() for window in window_manager.windows}
        try:
            result = bpy.ops.wm.window_new()
        except Exception as exc:
            self.report({'ERROR'}, _("Failed to open Text Editor window."))
            logger.error("Exception while creating new window: %s", exc)
            return {'CANCELLED'}

        if result != {'FINISHED'}:
            self.report({'ERROR'}, _("Failed to open Text Editor window."))
            logger.error("Operator wm.window_new returned %s", result)
            return {'CANCELLED'}

        windows_after = {
            window.as_pointer(): window for window in window_manager.windows
        }
        new_windows = [
            window for ptr, window in windows_after.items() if ptr not in windows_before
        ]
        if not new_windows:
            self.report({'ERROR'}, _("Failed to open Text Editor window."))
            logger.error("No new window detected after wm.window_new call.")
            return {'CANCELLED'}

        new_window = new_windows[-1]
        screen = getattr(new_window, "screen", None)
        if screen is None:
            self.report({'ERROR'}, _("Failed to open Text Editor window."))
            logger.error("New window has no screen to configure.")
            return {'CANCELLED'}

        target_area = None
        for area in screen.areas:
            if area.type == 'TEXT_EDITOR':
                target_area = area
                break

        if target_area is None:
            if not screen.areas:
                self.report({'ERROR'}, _("Failed to open Text Editor window."))
                logger.error("New window screen has no areas to convert.")
                return {'CANCELLED'}
            target_area = screen.areas[0]
            try:
                target_area.type = 'TEXT_EDITOR'
            except Exception as exc:
                self.report({'ERROR'}, _("Failed to open Text Editor window."))
                logger.error("Failed to convert area to Text Editor: %s", exc)
                return {'CANCELLED'}

        logger.info("Opened new Text Editor window for prompt editing.")
        return {'FINISHED'}


class MH3D_OT_NewText(Operator):
    bl_idname = "mh3d.new_text"
    bl_label = _("New Text")
    bl_description = _("Create a new Blender Text datablock for prompt editing.")

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = _get_settings(context)
        if settings is None:
            self.report({'ERROR'}, _("Settings unavailable."))
            logger.error("Cannot create text because settings are missing.")
            return {'CANCELLED'}

        base_name = "mh3d_prompt"
        text = bpy.data.texts.new(name=base_name)
        settings.prompt_text_name = text.name
        logger.info("Created new text datablock '%s' for prompt source.", text.name)
        return {'FINISHED'}


class MH3D_OT_SaveTextToFile(Operator):
    bl_idname = "mh3d.save_text_to_file"
    bl_label = _("Save Text to File")
    bl_description = _("Save the selected text datablock to an external file.")

    filepath: StringProperty(
        name=_("Prompt File"),
        subtype='FILE_PATH',
        options={'SKIP_SAVE'},
    )
    filter_glob: StringProperty(
        default="*.txt;*.md;*.prompt;*.json;*.*",
        options={'HIDDEN'},
    )

    def _ensure_text(self, context: bpy.types.Context) -> bpy.types.Text | None:
        settings = _get_settings(context)
        text = _get_selected_text(settings)
        if text is None:
            self.report({'ERROR'}, _("No text block selected."))
            logger.warning("Text block missing for operator %s.", type(self).__name__)
            return None
        return text

    def invoke(self, context: bpy.types.Context, event) -> set[str]:
        text = self._ensure_text(context)
        if text is None:
            return {'CANCELLED'}
        existing_path = getattr(text, "filepath", "")
        if existing_path:
            resolved = bpy.path.abspath(existing_path)
            if resolved:
                self.filepath = resolved
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context: bpy.types.Context) -> set[str]:
        text = self._ensure_text(context)
        if text is None:
            return {'CANCELLED'}
        path = bpy.path.abspath(self.filepath)
        if not path:
            self.report({'ERROR'}, _("File path is empty."))
            logger.warning("Save path empty when trying to export text.")
            return {'CANCELLED'}

        content = text.as_string() if hasattr(text, "as_string") else "\n".join(
            line.body for line in text.lines
        )
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")
        try:
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(normalized)
        except OSError as exc:
            self.report({'ERROR'}, str(exc))
            logger.error("Failed to save text to '%s': %s", path, exc)
            return {'CANCELLED'}

        text.filepath = path
        logger.info("Saved text datablock '%s' to '%s'.", text.name, path)
        return {'FINISHED'}


class MH3D_OT_LoadFileToText(Operator):
    bl_idname = "mh3d.load_file_to_text"
    bl_label = _("Load File to Text")
    bl_description = _("Load an external text file into the selected text datablock.")

    filepath: StringProperty(
        name=_("Prompt File"),
        subtype='FILE_PATH',
        options={'SKIP_SAVE'},
    )
    filter_glob: StringProperty(
        default="*.txt;*.md;*.prompt;*.json;*.*",
        options={'HIDDEN'},
    )

    def _ensure_text(self, context: bpy.types.Context) -> bpy.types.Text | None:
        settings = _get_settings(context)
        text = _get_selected_text(settings)
        if text is None:
            self.report({'ERROR'}, _("No text block selected."))
            logger.warning("Text block missing for operator %s.", type(self).__name__)
            return None
        return text

    def invoke(self, context: bpy.types.Context, event) -> set[str]:
        text = self._ensure_text(context)
        if text is None:
            return {'CANCELLED'}
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context: bpy.types.Context) -> set[str]:
        text = self._ensure_text(context)
        if text is None:
            return {'CANCELLED'}
        path = bpy.path.abspath(self.filepath)
        if not path:
            self.report({'ERROR'}, _("File path is empty."))
            logger.warning("Load path empty when trying to import text.")
            return {'CANCELLED'}
        try:
            with open(path, "rb") as handle:
                raw = handle.read()
        except OSError as exc:
            self.report({'ERROR'}, _("Failed to read prompt from file."))
            logger.error("Failed to read prompt file '%s': %s", path, exc)
            return {'CANCELLED'}

        decoded = raw.decode("utf-8", errors="replace")
        normalized = decoded.replace("\r\n", "\n").replace("\r", "\n")
        text.clear()
        text.write(normalized)
        text.filepath = path
        logger.info("Loaded file '%s' into text datablock '%s'.", path, text.name)
        return {'FINISHED'}


_CLASSES = (
    MH3D_OT_OpenTextEditor,
    MH3D_OT_NewText,
    MH3D_OT_SaveTextToFile,
    MH3D_OT_LoadFileToText,
)


def register() -> None:
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    logger.info("Text tool operators registered.")


def unregister() -> None:
    for cls in reversed(_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
    logger.info("Text tool operators unregistered.")

