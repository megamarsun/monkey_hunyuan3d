# -*- coding: utf-8 -*-
"""Addon preferences for Monkey hunyuan3D."""

from __future__ import annotations

import os

import bpy
from bpy.app.translations import pgettext_iface as _

from . import ADDON_ID, get_logger

logger = get_logger()


def _env_status(name: str) -> str:
    return _("Set") if os.environ.get(name) else _("Not set")


class MH3D_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = ADDON_ID

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        box = layout.box()
        box.label(text=_("Environment Variables"), icon='PREFERENCES')
        col = box.column(align=True)
        col.label(
            text=_("TENCENTCLOUD_SECRET_ID: {status}").format(
                status=_env_status("TENCENTCLOUD_SECRET_ID")
            )
        )
        col.label(
            text=_("TENCENTCLOUD_SECRET_KEY: {status}").format(
                status=_env_status("TENCENTCLOUD_SECRET_KEY")
            )
        )
        layout.label(
            text=_("Secrets typed in the panel are session-only and not saved."),
            icon='INFO',
        )
        layout.label(
            text=_("Set environment variables for production use."),
            icon='LOCKED',
        )


_CLASSES = (MH3D_AddonPreferences,)


def register() -> None:
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    logger.info("Preferences registered.")


def unregister() -> None:
    for cls in reversed(_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
    logger.info("Preferences unregistered.")
