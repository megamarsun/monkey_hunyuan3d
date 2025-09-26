# -*- coding: utf-8 -*-
"""Monkey Hunyuan3D Blender add-on package."""

from __future__ import annotations

import logging
import sys
from typing import Iterable

import bpy
from bpy.app.translations import pgettext_iface as _
from bpy.props import (
    BoolProperty,
    EnumProperty,
    PointerProperty,
    StringProperty,
)

__all__ = (
    "bl_info",
    "register",
    "unregister",
    "ADDON_ID",
    "get_logger",
    "DEFAULT_REGION",
)


bl_info = {
    "name": "Monkey hunyuan3D",
    "author": "Sakaki Masamune",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "3D View > Sidebar > Monkey hunyuan3D",
    "description": (
        "Connects Blender to Tencent Cloud Hunyuan3D 3.0 API to generate and import assets."
    ),
    "category": "3D View",
}


ADDON_ID = (__package__ or "monkey_hunyuan3d").split(".")[0]
_LOGGER_NAME = ADDON_ID
DEFAULT_REGION = "ap-guangzhou"


def get_logger() -> logging.Logger:
    """Return the package logger configured for console output."""
    logger = logging.getLogger(_LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(
            logging.Formatter("[MonkeyHunyuan3D] %(levelname)s: %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


logger = get_logger()


class MH3DSettings(bpy.types.PropertyGroup):
    """Shared settings stored on the scene."""

    input_mode: EnumProperty(
        name=_("Input Mode"),
        description=_("Choose how to provide input to Hunyuan3D."),
        items=(
            ("PROMPT", "Prompt", _("Use text prompt only")),
            ("IMAGE", "Image", _("Use local image file (Base64)")),
        ),
        default="IMAGE",
    )
    prompt_source: EnumProperty(
        name=_("Prompt Source"),
        description=_("Where to read the prompt text in PROMPT mode."),
        items=(
            ("INLINE", "Inline", _("Use inline textbox.")),
            ("TEXT_BLOCK", "Text Block", _("Use a Blender Text datablock.")),
            ("EXTERNAL_FILE", "External File", _("Load from a file on disk.")),
        ),
        default="INLINE",
    )
    prompt: StringProperty(
        name=_("Prompt"),
        description=_("Prompt used for Hunyuan3D generation."),
        default="a cute robot toy",
    )
    prompt_text_name: StringProperty(
        name=_("Text Block"),
        description=_("Name of the Blender Text datablock used as prompt source."),
        default="",
    )
    prompt_file_path: StringProperty(
        name=_("Prompt File"),
        description=_("External file path for prompt source."),
        subtype='FILE_PATH',
        default="",
        options={"SKIP_SAVE"},
    )
    image_path: StringProperty(
        name=_("Image"),
        description=_("Local image file used as reference for generation."),
        subtype='FILE_PATH',
        default="",
        options={"SKIP_SAVE"},
    )
    result_format: EnumProperty(
        name=_("Result Format"),
        description=_("File format of the generated asset."),
        items=(
            ("GLB", "GLB", _("Download model as glTF Binary (.glb).")),
            ("OBJ", "OBJ", _("Download model as Wavefront OBJ.")),
            ("FBX", "FBX", _("Download model as Autodesk FBX.")),
        ),
        default="GLB",
    )
    enable_pbr: BoolProperty(
        name=_("Enable PBR"),
        description=_("Request physically based rendering materials when supported."),
        default=False,
    )
    region: EnumProperty(
        name=_("Region"),
        description=_("Tencent Cloud region used for the Hunyuan3D service."),
        items=(
            (
                "ap-guangzhou",
                "ap-guangzhou",
                _("Use the ap-guangzhou region."),
            ),
            (
                "ap-shanghai",
                "ap-shanghai",
                _("Use the ap-shanghai region."),
            ),
            (
                "ap-singapore",
                "ap-singapore",
                _("Use the ap-singapore region."),
            ),
        ),
        default=DEFAULT_REGION,
    )
    secret_id: StringProperty(
        name=_("SecretId"),
        description=_("Fallback SecretId when environment variables are unavailable."),
        default="",
        options={"SKIP_SAVE"},
    )
    secret_key: StringProperty(
        name=_("SecretKey"),
        description=_("Fallback SecretKey when environment variables are unavailable."),
        default="",
        subtype='PASSWORD',
        options={"SKIP_SAVE"},
    )
    job_id: StringProperty(
        name=_("JobId"),
        description=_("Last submitted job identifier."),
        default="",
        options={"SKIP_SAVE"},
    )
    last_status: StringProperty(
        name=_("Status"),
        description=_("Last known status reported by the API."),
        default="",
        options={"SKIP_SAVE"},
    )
    last_error: StringProperty(
        name=_("Last Error"),
        description=_("Last error message reported by the API or importer."),
        default="",
        options={"SKIP_SAVE"},
    )


_CLASSES: Iterable[type[bpy.types.PropertyGroup]] = (MH3DSettings,)


def _register_properties() -> None:
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.mh3d_settings = PointerProperty(type=MH3DSettings)


def _unregister_properties() -> None:
    if hasattr(bpy.types.Scene, "mh3d_settings"):
        del bpy.types.Scene.mh3d_settings
    for cls in reversed(tuple(_CLASSES)):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass


def register() -> None:
    logger.info("Registering Monkey hunyuan3D add-on core.")
    from . import i18n, ops_deps, ops_generate, ops_text_tools, prefs, ui_panel

    _register_properties()
    prefs.register()
    ops_deps.register()
    ops_generate.register()
    ops_text_tools.register()
    ui_panel.register()
    i18n.register()
    logger.info("Monkey hunyuan3D add-on registered.")


def unregister() -> None:
    logger.info("Unregistering Monkey hunyuan3D add-on core.")
    from . import i18n, ops_deps, ops_generate, ops_text_tools, prefs, ui_panel

    i18n.unregister()
    ui_panel.unregister()
    ops_text_tools.unregister()
    ops_generate.unregister()
    ops_deps.unregister()
    prefs.unregister()
    _unregister_properties()
    logger.info("Monkey hunyuan3D add-on unregistered.")
