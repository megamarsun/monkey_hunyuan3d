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
        api_col.operator("mh3d.open_api_link", icon="URL")
        api_col.label(
            text=_("Production use of environment variables is recommended."),
            icon='INFO',
        )

        gen_box = layout.box()
        gen_box.label(text=_("Generation Settings"), icon='MODIFIER')
        gen_col = gen_box.column(align=True)
        gen_col.prop(settings, "prompt", text=_("Prompt"))
        gen_col.prop(settings, "result_format", text=_("Result Format"))
        gen_col.prop(settings, "enable_pbr", text=_("Enable PBR"))

        run_box = layout.box()
        run_box.label(text=_("Run"), icon='PLAY')
        run_box.operator("mh3d.generate", icon="PLAY")

        status_box = layout.box()
        status_box.label(text=_("Status"), icon='INFO')
        status_col = status_box.column(align=True)
        status_col.label(
            text=_("JobId: {job_id}").format(job_id=settings.job_id or _("-"))
        )
        status_col.label(
            text=_("Status: {status}").format(
                status=_format_status(settings.last_status)
            )
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
