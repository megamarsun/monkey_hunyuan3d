# -*- coding: utf-8 -*-
"""Operators that manage optional runtime dependencies."""

from __future__ import annotations

import bpy
from bpy.app.translations import pgettext_iface as _

from . import get_logger
from .utils_deps import ensure_package

logger = get_logger()


class MH3D_OT_InstallDeps(bpy.types.Operator):
    """Install required third-party dependencies into the add-on vendor directory."""

    bl_idname = "mh3d.install_deps"
    bl_label = _("Install Dependencies")
    bl_description = _(
        "Install Pillow and Tencent Cloud SDK into the add-on vendor folder."
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        try:
            ensure_package("PIL", "Pillow")
            ensure_package("tencentcloud", "tencentcloud-sdk-python")
        except Exception as exc:  # pragma: no cover - depends on user environment
            message = _("Failed to install dependencies: {error}").format(error=exc)
            self.report({'ERROR'}, message)
            logger.error(message)
            return {'CANCELLED'}
        success = _("Dependencies installed successfully.")
        self.report({'INFO'}, success)
        logger.info(success)
        return {'FINISHED'}


_CLASSES = (MH3D_OT_InstallDeps,)


def register() -> None:
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    logger.info("Dependency operators registered.")


def unregister() -> None:
    for cls in reversed(_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
    logger.info("Dependency operators unregistered.")
