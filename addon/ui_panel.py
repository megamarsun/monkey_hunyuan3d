# -*- coding: utf-8 -*-
"""User interface for the Monkey hunyuan3D add-on."""

from __future__ import annotations

import os

import bpy
from bpy.app.translations import pgettext_iface as _
from bpy.props import StringProperty
from bpy.types import UIList
from bpy_extras.io_utils import ImportHelper

from . import get_logger

logger = get_logger()

_STATUS_TRANSLATIONS = {
    "": "-",
    "SUBMITTING": "Submitting",
    "SUBMITTED": "Submitted",
    "QUEUED": "Queued",
    "QUEUING": "Queued",
    "PENDING": "Pending",
    "PROCESSING": "Processing",
    "RUNNING": "Running",
    "DONE": "Done",
    "SUCCEED": "Done",
    "SUCCEEDED": "Done",
    "SUCCESS": "Done",
    "IMPORTING": "Importing",
    "IMPORTED": "Imported",
    "FAIL": "Failed",
    "FAILED": "Failed",
    "ERROR": "Error",
    "UNKNOWN": "Unknown",
}


def _format_status(value: str) -> str:
    key = (value or "").upper()
    label = _STATUS_TRANSLATIONS.get(key)
    if label is not None:
        return _(label)
    return value or _("-")


class MH3D_UL_ImageList(UIList):
    bl_idname = "MH3D_UL_image_list"

    def draw_item(
        self,
        _context: bpy.types.Context,
        layout: bpy.types.UILayout,
        _data: bpy.types.PropertyGroup,
        item: bpy.types.PropertyGroup,
        _icon: int,
        _active_data: bpy.types.PropertyGroup,
        _active_propname: str,
        _index: int,
    ) -> None:
        value = getattr(item, "value", "")
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "value", text="", emboss=False, icon='IMAGE_DATA')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="🖼")


class MH3D_OT_ImageListAdd(bpy.types.Operator, ImportHelper):
    bl_idname = "mh3d.image_list_add"
    bl_label = _("Add Image Entry")
    bl_description = _("Add a new image entry according to the selected source.")

    filter_glob: StringProperty(default="*.png;*.jpg;*.jpeg;*.webp;*.bmp", options={'HIDDEN'})

    def _add_file_items(self, settings: bpy.types.PropertyGroup) -> None:
        directory = getattr(self, "directory", "")
        files = getattr(self, "files", None)
        if files:
            for element in files:
                name = getattr(element, "name", "")
                if not name:
                    continue
                path = os.path.join(directory, name)
                item = settings.image_files.add()
                item.value = path
        else:
            filepath = getattr(self, "filepath", "")
            if filepath:
                item = settings.image_files.add()
                item.value = filepath

    def execute(self, context: bpy.types.Context) -> set[str]:
        scene = context.scene
        if not scene:
            return {'CANCELLED'}
        settings = getattr(scene, "mh3d_settings", None)
        if settings is None:
            return {'CANCELLED'}
        source = settings.image_source
        if source == 'FILE':
            self._add_file_items(settings)
        elif source == 'URL':
            item = settings.image_files.add()
            item.value = "https://"
        else:
            item = settings.image_files.add()
            item.value = ""
        settings.image_files_index = max(0, len(settings.image_files) - 1)
        return {'FINISHED'}

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        scene = context.scene
        settings = getattr(scene, "mh3d_settings", None) if scene else None
        if settings and settings.image_source == 'FILE':
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}
        return self.execute(context)


class MH3D_OT_ImageListRemove(bpy.types.Operator):
    bl_idname = "mh3d.image_list_remove"
    bl_label = _("Remove Image Entry")
    bl_description = _("Remove the selected image entry from the list.")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        scene = context.scene
        settings = getattr(scene, "mh3d_settings", None) if scene else None
        return bool(settings and settings.image_files)

    def execute(self, context: bpy.types.Context) -> set[str]:
        scene = context.scene
        settings = getattr(scene, "mh3d_settings", None)
        if settings is None or not settings.image_files:
            return {'CANCELLED'}
        index = max(0, min(settings.image_files_index, len(settings.image_files) - 1))
        settings.image_files.remove(index)
        settings.image_files_index = max(0, len(settings.image_files) - 1)
        return {'FINISHED'}


class MH3D_PT_MainPanel(bpy.types.Panel):
    bl_label = _("Monkey hunyuan3D")
    bl_idname = "MH3D_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Monkey hunyuan3D"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene = context.scene
        settings = getattr(scene, "mh3d_settings", None)
        if settings is None:
            layout.label(text=_("Settings unavailable."), icon='ERROR')
            return

        api_box = layout.box()
        api_box.label(text=_("API Authentication"), icon='LOCKED')
        api_col = api_box.column(align=True)
        api_col.prop(settings, "secret_id", text=_("SecretId"))
        api_col.prop(settings, "secret_key", text=_("SecretKey"))
        api_col.operator("mh3d.open_api_link", icon="URL")
        api_col.label(
            text=_("Production use of environment variables is recommended."),
            icon='INFO',
        )

        gen_box = layout.box()
        gen_box.label(text=_("Generation Settings"), icon='MODIFIER')
        gen_col = gen_box.column(align=True)
        gen_col.prop(settings, "input_mode", text=_("Input Mode"))
        if settings.input_mode in {"TEXT", "TEXT_IMAGE"}:
            gen_col.prop(settings, "prompt", text=_("Prompt"))
        gen_col.prop(settings, "api_target", text=_("API Target"))
        if settings.input_mode in {"IMAGE", "TEXT_IMAGE"}:
            gen_col.prop(settings, "image_source", text=_("Image Source"))
            gen_col.prop(settings, "multi_view", text=_("Multi-view"))
            hint = _(
                "External APIs prefer URLs. Local services are often more reliable with base64."
            )
            gen_col.label(text=hint, icon='INFO')
            if settings.image_source == 'BASE64':
                limit_row = gen_col.row()
                limit_row.prop(settings, "image_b64_limit_mb", text=_("Base64 Limit (MB)"))
            if settings.multi_view:
                list_row = gen_col.row()
                list_row.template_list(
                    "MH3D_UL_image_list",
                    "",
                    settings,
                    "image_files",
                    settings,
                    "image_files_index",
                    rows=3,
                )
                ops_col = list_row.column(align=True)
                ops_col.operator("mh3d.image_list_add", icon='ADD', text="")
                ops_col.operator("mh3d.image_list_remove", icon='REMOVE', text="")
                if settings.image_files and 0 <= settings.image_files_index < len(settings.image_files):
                    active_item = settings.image_files[settings.image_files_index]
                    edit_box = gen_col.box()
                    label = {
                        'URL': _("Image URL"),
                        'FILE': _("Image Path"),
                        'BASE64': _("Image (base64)"),
                    }.get(settings.image_source, _("Image"))
                    edit_box.prop(active_item, "value", text=label)
            else:
                if settings.image_source == 'URL':
                    gen_col.prop(settings, "image_url", text=_("Image URL"))
                elif settings.image_source == 'BASE64':
                    gen_col.prop(settings, "image_b64", text=_("Image (base64)"))
                    gen_col.label(
                        text=_(
                            "Large base64 payloads may fail. Consider staying below {limit} MB."
                        ).format(limit=settings.image_b64_limit_mb),
                        icon='INFO',
                    )
                else:  # FILE
                    file_row = gen_col.row(align=True)
                    file_row.operator("mh3d.image_list_add", icon='FILEBROWSER', text=_("Select File"))
                    if settings.image_files:
                        first_item = settings.image_files[min(
                            settings.image_files_index, len(settings.image_files) - 1
                        )]
                        gen_col.prop(first_item, "value", text=_("Image Path"))
                    else:
                        gen_col.label(text=_("No file selected."), icon='INFO')
        gen_col.prop(settings, "result_format", text=_("Result Format"))
        gen_col.prop(settings, "enable_pbr", text=_("Enable PBR"))
        gen_col.prop(settings, "front_mask", text=_("Front Mask"))
        gen_col.prop(settings, "region", text=_("Region"))

        run_box = layout.box()
        run_box.label(text=_("Run"), icon='PLAY')
        run_box.operator("mh3d.generate", icon="PLAY")

        status_box = layout.box()
        status_box.label(text=_("Status"), icon='INFO')
        status_col = status_box.column(align=True)
        status_col.label(
            text=_("JobId: {job_id}").format(job_id=settings.job_id or _("-"))
        )
        readable_status = _format_status(settings.last_status)
        raw_status = settings.last_status or _("-")
        status_col.label(
            text=_("Status: {status}").format(status=readable_status)
        )
        status_col.label(
            text=_("Raw Status: {status}").format(status=raw_status)
        )
        error_text = settings.last_error.strip()
        status_col.label(
            text=_("Last Error: {message}").format(
                message=error_text or _("-")
            ),
            icon='ERROR' if error_text else 'CHECKMARK',
        )
        summary_text = settings.last_request_summary.strip()
        status_col.label(
            text=_("Last Request: {summary}").format(
                summary=summary_text or _("-"),
            ),
            icon='FILE_TICK' if summary_text else 'INFO',
        )


_CLASSES = (
    MH3D_UL_ImageList,
    MH3D_OT_ImageListAdd,
    MH3D_OT_ImageListRemove,
    MH3D_PT_MainPanel,
)


def register() -> None:
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    logger.info("UI panel registered.")


def unregister() -> None:
    for cls in reversed(_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
    logger.info("UI panel unregistered.")
