# -*- coding: utf-8 -*-
"""Operators for managing API secrets."""

from __future__ import annotations

import bpy
from bpy.app.translations import pgettext_iface as _

from . import get_logger
from .secret_storage import (
    SecretStorageError,
    clear_disk_password,
    clear_session_secret,
    get_session_password,
    has_encrypted_secret,
    load_encrypted_secret,
    load_password_from_disk,
    save_encrypted_secret,
    save_password_to_disk,
    set_session_password,
    set_session_secret,
)

logger = get_logger()


class MH3D_OT_SaveSecrets(bpy.types.Operator):
    """Encrypt and persist API secrets based on the selected mode."""

    bl_idname = "mh3d.save_secrets"
    bl_label = _("Encrypt Secrets")
    bl_description = _("Encrypt and store the API secrets based on the selected storage mode.")
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        scene = context.scene
        settings = getattr(scene, "mh3d_settings", None)
        if settings is None:
            self.report({'ERROR'}, _("Settings unavailable."))
            return {'CANCELLED'}

        secret_id = settings.secret_id.strip()
        secret_key = settings.secret_key.strip()
        mode = settings.secret_storage_mode
        password_input = settings.secret_password.strip()
        remember_password = settings.secret_remember_password

        if not secret_id or not secret_key:
            self.report({'ERROR'}, _("SecretId/SecretKey are required."))
            return {'CANCELLED'}

        if mode == 'NONE':
            clear_session_secret()
            set_session_password(None)
            settings.secret_id = ""
            settings.secret_key = ""
            settings.secret_password = ""
            self.report({'INFO'}, _("NONE mode does not store secrets. They must be typed each time."))
            return {'FINISHED'}

        if mode == 'SESSION':
            set_session_secret(secret_id, secret_key)
            if password_input:
                set_session_password(password_input)
            else:
                set_session_password(None)
            settings.secret_id = ""
            settings.secret_key = ""
            settings.secret_password = ""
            self.report({'INFO'}, _("Secrets stored in session memory until Blender closes."))
            return {'FINISHED'}

        # DISK mode
        password = password_input or get_session_password() or load_password_from_disk()
        if not password:
            self.report({'ERROR'}, _("Password is required for disk mode."))
            return {'CANCELLED'}

        try:
            save_encrypted_secret(secret_id, secret_key, password)
        except SecretStorageError as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}

        set_session_secret(secret_id, secret_key)
        set_session_password(password)

        if remember_password:
            save_password_to_disk(password)
        else:
            clear_disk_password()

        settings.secret_id = ""
        settings.secret_key = ""
        settings.secret_password = ""
        self.report({'INFO'}, _("Secrets encrypted and stored on disk."))
        return {'FINISHED'}


class MH3D_OT_TestSecrets(bpy.types.Operator):
    """Verify that stored secrets can be decrypted."""

    bl_idname = "mh3d.test_secrets"
    bl_label = _("Test Secret Decryption")
    bl_description = _("Test decrypting the stored secrets using the available password sources.")
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        scene = context.scene
        settings = getattr(scene, "mh3d_settings", None)
        if settings is None:
            self.report({'ERROR'}, _("Settings unavailable."))
            return {'CANCELLED'}

        password = settings.secret_password.strip() or get_session_password() or load_password_from_disk()
        settings.secret_password = ""

        if not has_encrypted_secret():
            self.report({'ERROR'}, _("No encrypted secret found on disk."))
            return {'CANCELLED'}

        if not password:
            self.report({'ERROR'}, _("Password not available for decryption."))
            return {'CANCELLED'}

        try:
            secret = load_encrypted_secret(password)
        except SecretStorageError as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}

        if not secret.secret_id or not secret.secret_key:
            self.report({'ERROR'}, _("Decrypted secret is empty."))
            return {'CANCELLED'}

        self.report({'INFO'}, _("Decryption succeeded. Secrets are available."))
        return {'FINISHED'}


_CLASSES = (
    MH3D_OT_SaveSecrets,
    MH3D_OT_TestSecrets,
)


def register() -> None:
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    logger.info("Secret operators registered.")


def unregister() -> None:
    for cls in reversed(_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
    logger.info("Secret operators unregistered.")
