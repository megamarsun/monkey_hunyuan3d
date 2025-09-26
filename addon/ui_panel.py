# -*- coding: utf-8 -*-
"""User interface for the Monkey hunyuan3D add-on."""

from __future__ import annotations

import bpy
from bpy.app.translations import pgettext_iface as _

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
        api_col.prop(settings, "secret_password")
        api_col.prop(settings, "secret_storage_mode")
        if settings.secret_storage_mode == 'DISK':
            warn_col = api_col.column(align=True)
            warn_col.alert = True
            warn_col.label(
                text=_("Local disk storage is vulnerable; enable only if you accept the risk."),
                icon='ERROR',
            )
            api_col.prop(settings, "secret_remember_password")
            if settings.secret_remember_password:
                api_col.label(
                    text=_("Storing the password is your responsibility. Physical access may expose it."),
                    icon='INFO',
                )
        else:
            disabled_row = api_col.row(align=True)
            disabled_row.enabled = False
            disabled_row.prop(settings, "secret_remember_password", toggle=True)
        ops_row = api_col.row(align=True)
        ops_row.operator("mh3d.save_secrets", icon='DISK_DRIVE')
        ops_row.operator("mh3d.test_secrets", icon='FILE_REFRESH')
        api_col.operator("mh3d.open_api_link", icon="URL")
        api_col.label(
            text=_("Production use of environment variables is recommended."),
            icon='INFO',
        )

        input_box = layout.box()
        input_box.label(text=_("Input Mode"), icon='FILE_IMAGE')
        mode_row = input_box.row(align=True)
        mode_row.prop(settings, "input_mode", expand=True)

        mode_value = getattr(settings, "input_mode", "IMAGE")
        if mode_value == "PROMPT":
            prompt_col = input_box.column(align=True)
            prompt_col.prop(settings, "prompt_source", text=_("Prompt Source"))
            source = getattr(settings, "prompt_source", "INLINE")
            if source == "TEXT_BLOCK":
                prompt_col.prop_search(
                    settings,
                    "prompt_text_name",
                    bpy.data,
                    "texts",
                    text=_("Text Block"),
                )
                editor_row = prompt_col.row(align=True)
                editor_row.operator("mh3d.open_text_editor", icon='FILE_TEXT')
                editor_row.operator("mh3d.new_text", icon='ADD')
                file_row = prompt_col.row(align=True)
                file_row.operator("mh3d.save_text_to_file", icon='FILE_TICK')
                file_row.operator("mh3d.load_file_to_text", icon='FILE_FOLDER')
            elif source == "EXTERNAL_FILE":
                file_col = prompt_col.column(align=True)
                file_col.prop(settings, "prompt_file_path", text=_("Prompt File"))
                file_col.label(text=_("UTF-8 expected. CRLF normalized."), icon='INFO')
            else:
                inline_col = prompt_col.column(align=True)
                inline_col.scale_y = 1.4
                inline_col.prop(settings, "prompt", text=_("Prompt"))
        else:
            input_box.prop(settings, "image_path", text=_("Image File"))
            input_box.label(
                text=_(
                    "Images under 8MB after encoding are supported. Large files are recompressed automatically."
                ),
                icon='INFO',
            )

        gen_box = layout.box()
        gen_box.label(text=_("Generation Settings"), icon='MODIFIER')
        gen_col = gen_box.column(align=True)
        gen_col.prop(settings, "result_format", text=_("Result Format"))
        gen_col.prop(settings, "enable_pbr", text=_("Enable PBR"))
        gen_col.prop(settings, "region", text=_("Region"))

        run_box = layout.box()
        run_box.label(text=_("Run"), icon='PLAY')
        run_box.operator("mh3d.generate", icon="PLAY")
        run_box.operator("mh3d.install_deps", icon='IMPORT')

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


_CLASSES = (MH3D_PT_MainPanel,)


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
