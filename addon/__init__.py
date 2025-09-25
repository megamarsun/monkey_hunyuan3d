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
    CollectionProperty,
    EnumProperty,
    IntProperty,
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
    "version": (0, 2, 0),
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


class MH3DImageItem(bpy.types.PropertyGroup):
    """Generic container for image related user input."""

    value: StringProperty(
        name=_("Value"),
        description=_("Path, URL or base64 string representing an image."),
        default="",
        options={"SKIP_SAVE"},
    )


class MH3DSettings(bpy.types.PropertyGroup):
    """Shared settings stored on the scene."""

    prompt: StringProperty(
        name=_("Prompt"),
        description=_("Prompt used for Hunyuan3D generation."),
        default="a cute robot toy",
    )
    input_mode: EnumProperty(
        name=_("Input Mode"),
        description=_("Select how prompts and images are combined."),
        items=(
            ("TEXT", _("Text"), _("Generate using text prompt only.")),
            (
                "IMAGE",
                _("Image"),
                _("Generate using image guidance without a text prompt."),
            ),
            (
                "TEXT_IMAGE",
                _("Text + Image"),
                _("Generate using both text prompt and image guidance."),
            ),
        ),
        default="TEXT",
    )
    image_source: EnumProperty(
        name=_("Image Source"),
        description=_("Choose how reference images are provided."),
        items=(
            ("URL", _("URL"), _("Use an external URL to reference the image.")),
            (
                "FILE",
                _("File"),
                _("Upload a local file that will be base64 encoded before submission."),
            ),
            (
                "BASE64",
                _("Base64"),
                _("Paste raw base64 data representing the image."),
            ),
        ),
        default="URL",
    )
    image_url: StringProperty(
        name=_("Image URL"),
        description=_("Single image URL when not using multi-view."),
        default="",
        options={"SKIP_SAVE"},
    )
    image_b64: StringProperty(
        name=_("Image (base64)"),
        description=_("Single base64 image payload when not using multi-view."),
        default="",
        options={"SKIP_SAVE"},
    )
    image_files: CollectionProperty(type=MH3DImageItem, options={"SKIP_SAVE"})
    image_files_index: IntProperty(default=0, options={"SKIP_SAVE"})
    image_b64_limit_mb: IntProperty(
        name=_("Base64 Limit (MB)"),
        description=_("Soft limit for total decoded image bytes when using base64 uploads."),
        default=20,
        min=1,
        soft_max=200,
    )
    multi_view: BoolProperty(
        name=_("Multi-view"),
        description=_("Submit multiple reference images from different angles."),
        default=False,
    )
    front_mask: BoolProperty(
        name=_("Front Mask"),
        description=_("Request foreground masking when supported."),
        default=False,
    )
    api_target: EnumProperty(
        name=_("API Target"),
        description=_("Select the backend that will handle the generation request."),
        items=(
            (
                "TENCENT_CLOUD",
                _("Tencent Cloud"),
                _("Use Tencent Cloud's official Hunyuan3D 3.0 API."),
            ),
            (
                "LOCAL_SERVER",
                _("Local Server"),
                _("Send the request to a locally hosted wrapper service."),
            ),
            (
                "FAL",
                _("FAL"),
                _("Use FAL.ai hosted inference endpoints."),
            ),
            (
                "REPLICATE",
                _("Replicate"),
                _("Use Replicate hosted inference endpoints."),
            ),
        ),
        default="TENCENT_CLOUD",
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
    last_request_summary: StringProperty(
        name=_("Last Request"),
        description=_("Summary of the most recent submission payload."),
        default="",
        options={"SKIP_SAVE"},
    )


_CLASSES: Iterable[type[bpy.types.PropertyGroup]] = (
    MH3DImageItem,
    MH3DSettings,
)


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
    from . import i18n, ops_generate, prefs, ui_panel

    _register_properties()
    prefs.register()
    ops_generate.register()
    ui_panel.register()
    i18n.register()
    logger.info("Monkey hunyuan3D add-on registered.")


def unregister() -> None:
    logger.info("Unregistering Monkey hunyuan3D add-on core.")
    from . import i18n, ops_generate, prefs, ui_panel

    i18n.unregister()
    ui_panel.unregister()
    ops_generate.unregister()
    prefs.unregister()
    _unregister_properties()
    logger.info("Monkey hunyuan3D add-on unregistered.")
