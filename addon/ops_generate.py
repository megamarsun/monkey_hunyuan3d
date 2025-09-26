# -*- coding: utf-8 -*-
"""Operators for interacting with the Hunyuan3D API."""

from __future__ import annotations

import base64
import io
import json
import os
import shutil
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

import bpy
from bpy.app.translations import pgettext_iface as _
from bpy.types import Operator, Window

from . import ADDON_ID, DEFAULT_REGION, get_logger
from .secret_storage import (
    SecretStorageError,
    get_session_password,
    get_session_secret,
    load_encrypted_secret,
    load_password_from_disk,
    set_session_password,
    set_session_secret,
)
from .utils_deps import ensure_package

logger = get_logger()

API_ENDPOINT = "ai3d.tencentcloudapi.com"
API_VERSION = "2025-05-13"
POLL_INTERVAL = 2.0
MAX_IMAGE_BASE64_SIZE = 8 * 1024 * 1024
JPEG_QUALITY_STEPS = (95, 90, 85, 80, 75, 70, 65, 60)


@dataclass(frozen=True)
class _SDKBundle:
    credential_factory: Callable[[str, str], Any]
    client_profile_cls: Any
    http_profile_cls: Any
    client_cls: Any
    exception_cls: Any


def _import_sdk() -> _SDKBundle:
    try:
        from tencentcloud.common import credential
        from tencentcloud.common.abstract_client import AbstractClient
        from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
            TencentCloudSDKException,
        )
        from tencentcloud.common.profile.client_profile import ClientProfile
        from tencentcloud.common.profile.http_profile import HttpProfile
    except ImportError:
        try:
            ensure_package("tencentcloud", "tencentcloud-sdk-python")
        except Exception as exc:  # pragma: no cover - subprocess outcome
            raise RuntimeError(
                _("Failed to install Tencent Cloud SDK: {error}").format(error=exc)
            ) from exc
        try:
            from tencentcloud.common import credential
            from tencentcloud.common.abstract_client import AbstractClient
            from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
                TencentCloudSDKException,
            )
            from tencentcloud.common.profile.client_profile import ClientProfile
            from tencentcloud.common.profile.http_profile import HttpProfile
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(
                _(
                    "Failed to import Tencent Cloud SDK after installation attempt."
                )
            ) from exc

    class Hunyuan3DClient(AbstractClient):
        _apiVersion = API_VERSION
        _endpoint = API_ENDPOINT
        _service = "ai3d"

    def credential_factory(secret_id: str, secret_key: str) -> Any:
        return credential.Credential(secret_id, secret_key)

    return _SDKBundle(
        credential_factory=credential_factory,
        client_profile_cls=ClientProfile,
        http_profile_cls=HttpProfile,
        client_cls=Hunyuan3DClient,
        exception_cls=TencentCloudSDKException,
    )


def _create_client(
    bundle: _SDKBundle, secret_id: str, secret_key: str, region: Optional[str] = None
) -> Any:
    http_profile = bundle.http_profile_cls(endpoint=API_ENDPOINT)
    try:
        setattr(http_profile, "reqTimeout", 15)
    except Exception:
        pass
    client_profile = bundle.client_profile_cls(httpProfile=http_profile)
    cred = bundle.credential_factory(secret_id, secret_key)
    region_value = (region or DEFAULT_REGION).strip() or DEFAULT_REGION
    return bundle.client_cls(cred, region_value, client_profile)


def _download_file(url: str, suffix: str) -> str:
    tmp = tempfile.NamedTemporaryFile(prefix="mh3d_", suffix=suffix, delete=False)
    tmp_path = tmp.name
    tmp.close()
    try:
        with urllib.request.urlopen(url, timeout=30) as response, open(
            tmp_path, "wb"
        ) as handle:
            shutil.copyfileobj(response, handle)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
    return tmp_path


def _import_model(filepath: str, fmt: str) -> None:
    fmt_upper = fmt.upper()
    if fmt_upper == "GLB":
        bpy.ops.import_scene.gltf(filepath=filepath)
    elif fmt_upper == "OBJ":
        try:
            bpy.ops.wm.obj_import(filepath=filepath)
        except AttributeError:
            bpy.ops.import_scene.obj(filepath=filepath)
    elif fmt_upper == "FBX":
        bpy.ops.import_scene.fbx(filepath=filepath)
    else:  # pragma: no cover - defensive guard
        raise ValueError(f"Unsupported format: {fmt}")


def _suffix_for_format(fmt: str) -> str:
    return {
        "GLB": ".glb",
        "OBJ": ".obj",
        "FBX": ".fbx",
    }.get(fmt.upper(), ".bin")


def _encode_image_to_base64(path: str, target_max_bytes: int = MAX_IMAGE_BASE64_SIZE) -> str:
    if not path:
        raise ValueError("Image path is empty.")
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    try:
        ensure_package("PIL", "Pillow")
        from PIL import Image  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - environment dependent
        raise ImportError("pillow-autoinstall-failed") from exc

    try:
        with Image.open(path) as handle:
            try:
                img = handle.convert("RGB")
            except Exception as exc:  # pragma: no cover - depends on PIL backend
                raise ValueError(f"Failed to convert image: {exc}") from exc
    except Exception as exc:  # pragma: no cover - depends on user file
        raise ValueError(f"Failed to open image: {exc}") from exc

    for quality in JPEG_QUALITY_STEPS:
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        data = buffer.getvalue()
        encoded = base64.b64encode(data)
        if len(encoded) < target_max_bytes:
            return encoded.decode("ascii")

    raise ValueError("Encoded image exceeds size limit.")


def _normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _read_prompt_from_source(settings: bpy.types.PropertyGroup) -> str:
    source_value = getattr(settings, "prompt_source", "INLINE") or "INLINE"
    source = source_value.upper()
    if source == "TEXT_BLOCK":
        text_name = (getattr(settings, "prompt_text_name", "") or "").strip()
        if not text_name:
            logger.warning("Text block missing for prompt source.")
            raise ValueError("No text block selected.")
        text_block = bpy.data.texts.get(text_name)
        if text_block is None:
            logger.warning("Text block '%s' not found for prompt source.", text_name)
            raise ValueError("No text block selected.")
        raw_text = (
            text_block.as_string()
            if hasattr(text_block, "as_string")
            else "\n".join(line.body for line in text_block.lines)
        )
        normalized = _normalize_newlines(raw_text)
        prompt_text = normalized.strip()
    elif source == "EXTERNAL_FILE":
        file_setting = getattr(settings, "prompt_file_path", "") or ""
        resolved_path = bpy.path.abspath(file_setting)
        if not resolved_path:
            logger.warning("Prompt file path empty.")
            raise ValueError("File path is empty.")
        try:
            with open(resolved_path, "rb") as handle:
                raw = handle.read()
        except OSError as exc:
            logger.error("Failed to read prompt file '%s': %s", resolved_path, exc)
            raise ValueError("Failed to read prompt from file.") from exc
        decoded = raw.decode("utf-8", errors="replace")
        normalized = _normalize_newlines(decoded)
        prompt_text = normalized.strip()
    else:
        inline_prompt = getattr(settings, "prompt", "") or ""
        normalized = _normalize_newlines(inline_prompt)
        prompt_text = normalized.strip()

    if not prompt_text:
        logger.warning("Prompt text empty after reading source=%s.", source)
        raise ValueError("Prompt is empty.")

    logger.info("Prompt source=%s, length=%d", source, len(prompt_text))
    return prompt_text


class MH3D_OT_OpenAPILink(Operator):
    bl_idname = "mh3d.open_api_link"
    bl_label = _("Open API Key Page")
    bl_description = _("Open the Tencent Cloud API key management page in a browser.")

    def execute(self, context: bpy.types.Context) -> set[str]:
        import webbrowser

        url = "https://console.tencentcloud.com/cam/capi"
        try:
            webbrowser.open(url)
        except Exception as exc:  # pragma: no cover - depends on OS
            message = _("Failed to open browser: {error}").format(error=exc)
            self.report({'ERROR'}, message)
            logger.error(message)
            return {'CANCELLED'}
        self.report({'INFO'}, _("Opened Tencent Cloud API key page."))
        logger.info("Opening API key page: %s", url)
        return {'FINISHED'}


class MH3D_OT_Generate(Operator):
    bl_idname = "mh3d.generate"
    bl_label = _("Generate 3D")
    bl_description = _(
        "Submit a prompt to the Hunyuan3D API, then download and import the result when ready."
    )
    bl_options = {'REGISTER'}

    _active_job: Optional[str] = None
    _wait_cursor_count: int = 0
    _wait_cursor_windows: list[tuple[Window, str]] = []

    def _resolve_credentials(self, settings: bpy.types.PropertyGroup) -> tuple[str, str]:
        env_secret_id = os.environ.get("TENCENTCLOUD_SECRET_ID", "").strip()
        env_secret_key = os.environ.get("TENCENTCLOUD_SECRET_KEY", "").strip()
        if env_secret_id and env_secret_key:
            return env_secret_id, env_secret_key

        ui_secret_id = settings.secret_id.strip()
        ui_secret_key = settings.secret_key.strip()
        if ui_secret_id and ui_secret_key:
            return ui_secret_id, ui_secret_key

        session_secret = get_session_secret()
        if session_secret is not None:
            return session_secret.secret_id, session_secret.secret_key

        password_candidate = settings.secret_password.strip()
        if password_candidate:
            settings.secret_password = ""
        else:
            password_candidate = get_session_password() or ""
        if not password_candidate:
            try:
                password_candidate = load_password_from_disk() or ""
            except SecretStorageError as exc:
                self.report({'ERROR'}, str(exc))
                return "", ""

        if not password_candidate:
            return "", ""

        try:
            disk_secret = load_encrypted_secret(password_candidate)
        except SecretStorageError as exc:
            self.report({'ERROR'}, str(exc))
            return "", ""

        set_session_password(password_candidate)
        set_session_secret(disk_secret.secret_id, disk_secret.secret_key)
        return disk_secret.secret_id, disk_secret.secret_key

    @staticmethod
    def _friendly_hint(exc: Exception) -> str:
        text_parts = []
        for attr in ("code", "Code", "message", "Message"):
            value = getattr(exc, attr, "")
            if value:
                text_parts.append(str(value))
        text_parts.append(str(exc))
        merged = " ".join(text_parts)
        hints = (
            (
                "RequestLimitExceeded.JobNumExceed",
                _("Another job is running. Wait until it finishes."),
            ),
            (
                "UnsupportedRegion",
                _(
                    "This API is unavailable in the selected region. Try ap-guangzhou / ap-shanghai / ap-singapore."
                ),
            ),
            (
                "AuthFailure.SecretIdNotFound",
                _(
                    "Verify that your SecretId/SecretKey are correct and not disabled or deleted."
                ),
            ),
        )
        for key, hint in hints:
            if key and key in merged:
                return hint
        return ""

    def _format_sdk_error(self, prefix: str, exc: Exception) -> str:
        hint = self._friendly_hint(exc)
        if hint:
            return f"{prefix} {hint}"
        return prefix

    def _set_wait_cursor(self, context: bpy.types.Context) -> None:
        self._cursor_engaged = False
        manager = getattr(context, "window_manager", None)
        if manager is None:
            return
        windows: list[tuple[Window, str]] = []
        for window in getattr(manager, "windows", []):
            try:
                window.cursor_modal_set('WAIT')
                windows.append((window, "modal"))
            except Exception:
                try:
                    window.cursor_set('WAIT')
                    windows.append((window, "set"))
                except Exception:
                    continue
        if not windows:
            return
        cls = type(self)
        cls._wait_cursor_windows = windows
        cls._wait_cursor_count += 1
        self._cursor_engaged = True

    def _restore_cursor(self) -> None:
        if not getattr(self, "_cursor_engaged", False):
            return
        cls = type(self)
        if cls._wait_cursor_count > 0:
            cls._wait_cursor_count -= 1
        else:
            cls._wait_cursor_count = 0
        self._cursor_engaged = False
        if cls._wait_cursor_count > 0:
            return
        windows = cls._wait_cursor_windows
        cls._wait_cursor_windows = []
        for window, mode in windows:
            try:
                if mode == "modal":
                    window.cursor_modal_restore()
            except Exception:
                pass
            try:
                window.cursor_set('DEFAULT')
            except Exception:
                pass

    def execute(self, context: bpy.types.Context) -> set[str]:
        self._cursor_engaged = False
        scene = context.scene
        if not scene:
            self.report({'ERROR'}, _("No active scene found."))
            return {'CANCELLED'}
        settings = getattr(scene, "mh3d_settings", None)
        if settings is None:
            self.report({'ERROR'}, _("Settings are not available on the scene."))
            return {'CANCELLED'}

        input_mode = (getattr(settings, "input_mode", "IMAGE") or "IMAGE").upper()
        if input_mode not in {"PROMPT", "IMAGE"}:
            input_mode = "IMAGE"

        image_path_setting = getattr(settings, "image_path", "")
        prompt_text = ""
        if input_mode == "PROMPT" and image_path_setting:
            info_message = _("Prompt and image cannot be used together.")
            self.report({'INFO'}, info_message)
            logger.warning(
                "Image path provided while using PROMPT mode; ignoring image_path.",
            )

        image_b64: Optional[str] = None
        if input_mode == "PROMPT":
            try:
                prompt_text = _read_prompt_from_source(settings)
            except ValueError as exc:
                key = str(exc)
                translations = {
                    "No text block selected.": _("No text block selected."),
                    "File path is empty.": _("File path is empty."),
                    "Failed to read prompt from file.": _(
                        "Failed to read prompt from file."
                    ),
                    "Prompt is empty.": _("Prompt is empty."),
                }
                message = translations.get(key, str(exc))
                self.report({'ERROR'}, message)
                logger.error(message)
                return {'CANCELLED'}
        else:
            if not image_path_setting:
                message = _("Image mode requires a valid image file.")
                self.report({'ERROR'}, message)
                logger.error(message)
                return {'CANCELLED'}
            resolved_image_path = bpy.path.abspath(image_path_setting)
            if not resolved_image_path:
                message = _("Image mode requires a valid image file.")
                self.report({'ERROR'}, message)
                logger.error(message)
                return {'CANCELLED'}
            try:
                image_b64 = _encode_image_to_base64(resolved_image_path)
            except ImportError as exc:
                message = _(
                    "Failed to load Pillow. Use 'Install Dependencies' or check your network access."
                )
                self.report({'ERROR'}, message)
                logger.error("%s Error: %s", message, exc)
                return {'CANCELLED'}
            except FileNotFoundError:
                message = _("Image mode requires a valid image file.")
                self.report({'ERROR'}, message)
                logger.error(message)
                return {'CANCELLED'}
            except ValueError as exc:
                limit_key = "Encoded image exceeds size limit."
                empty_key = "Image path is empty."
                text = str(exc)
                if empty_key in text:
                    message = _("Image mode requires a valid image file.")
                elif limit_key in text:
                    message = _("Image is too large. Ensure the encoded size is under 8MB.")
                else:
                    message = _("Failed to prepare image: {error}").format(error=exc)
                self.report({'ERROR'}, message)
                logger.error(message)
                return {'CANCELLED'}
            except Exception as exc:  # pragma: no cover - defensive
                message = _("Failed to prepare image: {error}").format(error=exc)
                self.report({'ERROR'}, message)
                logger.error(message)
                return {'CANCELLED'}

        prompt_param_name = "Prompt"
        try:
            addon_entry = bpy.context.preferences.addons.get(ADDON_ID)
        except Exception:
            addon_entry = None
        if addon_entry is not None:
            candidate = getattr(getattr(addon_entry, "preferences", None), "prompt_param_name", "")
            if isinstance(candidate, str) and candidate.strip():
                prompt_param_name = candidate.strip()

        try:
            bundle = _import_sdk()
        except RuntimeError as exc:
            error_text = str(exc)
            self.report({'ERROR'}, error_text)
            logger.error(error_text)
            return {'CANCELLED'}

        secret_id, secret_key = self._resolve_credentials(settings)
        if not secret_id or not secret_key:
            message = _(
                "API keys missing: set environment variables or fill SecretId/SecretKey."
            )
            self.report({'ERROR'}, message)
            logger.error(message)
            return {'CANCELLED'}

        settings.last_error = ""
        settings.last_status = "SUBMITTING"
        settings.job_id = ""

        region = settings.region or DEFAULT_REGION
        client = _create_client(bundle, secret_id, secret_key, region)
        params: Dict[str, Any] = {
            "ResultFormat": settings.result_format,
        }
        if input_mode == "PROMPT":
            params[prompt_param_name] = prompt_text
        else:
            if not image_b64:
                message = _("Image mode requires a valid image file.")
                self.report({'ERROR'}, message)
                logger.error(message)
                return {'CANCELLED'}
            params["ImageBase64"] = image_b64
        reenable_pbr_after_success = not settings.enable_pbr
        if settings.enable_pbr:
            params["EnablePBR"] = True

        logger.info(
            "Submitting job with mode=%s, format=%s, pbr=%s",
            input_mode,
            settings.result_format,
            bool(settings.enable_pbr),
        )

        self._set_wait_cursor(context)
        try:
            response_raw = client.call("SubmitHunyuanTo3DJob", params)
            response = json.loads(response_raw).get("Response", {})
            job_id = response.get("JobId")
            if not job_id:
                raise ValueError("JobId missing in response.")
        except bundle.exception_cls as exc:  # type: ignore[attr-defined]
            base = _("API error during submission: {error}").format(error=str(exc))
            message = self._format_sdk_error(base, exc)
            settings.last_status = "ERROR"
            settings.last_error = message
            self._restore_cursor()
            self.report({'ERROR'}, message)
            logger.error("Submission failed: %s", exc)
            return {'CANCELLED'}
        except Exception as exc:
            message = _("Unexpected error during submission: {error}").format(error=exc)
            settings.last_status = "ERROR"
            settings.last_error = message
            self._restore_cursor()
            self.report({'ERROR'}, message)
            logger.error("Submission failed: %s", exc)
            return {'CANCELLED'}

        settings.job_id = job_id
        settings.last_status = response.get("Status", "SUBMITTED")
        self._active_job = job_id

        info_message = _("Job submitted. Tracking in the status panel.")
        self.report({'INFO'}, info_message)
        logger.info("Submitted job %s", job_id)

        def poll_job() -> Optional[float]:
            scene_inner = bpy.context.scene
            if not scene_inner or not hasattr(scene_inner, "mh3d_settings"):
                logger.warning("Scene missing while polling job %s; stopping timer.", job_id)
                self._restore_cursor()
                self._active_job = None
                return None
            settings_inner = scene_inner.mh3d_settings
            if settings_inner.job_id != job_id:
                logger.info(
                    "Job id changed (now %s). Stop polling previous job %s.",
                    settings_inner.job_id,
                    job_id,
                )
                self._restore_cursor()
                self._active_job = None
                return None

            try:
                client_inner = _create_client(bundle, secret_id, secret_key, region)
                raw = client_inner.call("QueryHunyuanTo3DJob", {"JobId": job_id})
                payload = json.loads(raw).get("Response", {})
                try:
                    logger.debug(
                        "Query response for job %s: %s",
                        job_id,
                        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
                    )
                except TypeError:
                    logger.debug("Query response for job %s (non-serializable)", job_id)
            except bundle.exception_cls as exc:  # type: ignore[attr-defined]
                base_inner = _("API error while querying job: {error}").format(
                    error=str(exc)
                )
                message_inner = self._format_sdk_error(base_inner, exc)
                settings_inner.last_status = "ERROR"
                settings_inner.last_error = message_inner
                logger.error("Query failed for job %s: %s", job_id, exc)
                self._restore_cursor()
                self._active_job = None
                return None
            except Exception as exc:  # pragma: no cover - depends on network state
                message_inner = _("Query error: {error}").format(error=exc)
                settings_inner.last_status = "ERROR"
                settings_inner.last_error = message_inner
                logger.error("Query failed for job %s: %s", job_id, exc)
                self._restore_cursor()
                self._active_job = None
                return None

            status = payload.get("Status") or payload.get("JobStatus") or ""
            status_upper = (status or "").upper()
            settings_inner.last_status = status_upper or "UNKNOWN"

            success_statuses = {"DONE", "SUCCEED", "SUCCEEDED", "SUCCESS"}
            failure_statuses = {"FAIL", "FAILED"}

            if status_upper not in success_statuses | failure_statuses:
                return POLL_INTERVAL
            if status_upper in success_statuses:
                files = payload.get("ResultFile3Ds") or []
                url = None
                if files:
                    url = files[0].get("Url") or files[0].get("URL")
                if not url:
                    settings_inner.last_error = _(
                        "Job completed but no download URL was returned."
                    )
                    settings_inner.last_status = "ERROR"
                    try:
                        payload_dump = json.dumps(
                            payload, ensure_ascii=False, indent=2, default=str
                        )
                    except TypeError:
                        payload_dump = str(payload)
                    logger.error(
                        "Job %s completed but returned no URL. Payload: %s",
                        job_id,
                        payload_dump,
                    )
                    self._restore_cursor()
                    self._active_job = None
                    return None
                suffix = _suffix_for_format(settings_inner.result_format)
                filepath = ""
                try:
                    filepath = _download_file(url, suffix)
                    logger.info("Downloaded job %s result to %s", job_id, filepath)
                    settings_inner.last_status = "IMPORTING"
                    _import_model(filepath, settings_inner.result_format)
                    settings_inner.last_status = "IMPORTED"
                    settings_inner.last_error = ""
                    logger.info("Imported job %s result successfully.", job_id)
                    if reenable_pbr_after_success and hasattr(
                        settings_inner, "enable_pbr"
                    ):
                        settings_inner.enable_pbr = True
                        logger.info(
                            "Re-enabled PBR after successful import for job %s.", job_id
                        )
                except urllib.error.URLError as exc:
                    message_inner = _("Download error: {error}").format(error=exc)
                    settings_inner.last_status = "ERROR"
                    settings_inner.last_error = message_inner
                    logger.error("Download failed for job %s: %s", job_id, exc)
                except Exception as exc:
                    message_inner = _("Import failed: {error}").format(error=exc)
                    settings_inner.last_status = "ERROR"
                    settings_inner.last_error = message_inner
                    logger.error("Import failed for job %s: %s", job_id, exc)
                finally:
                    if filepath and os.path.exists(filepath):
                        try:
                            os.remove(filepath)
                        except Exception:  # pragma: no cover - best effort cleanup
                            logger.warning("Failed to remove temporary file %s", filepath)
                self._restore_cursor()
                self._active_job = None
                return None
            if status_upper in failure_statuses:
                error_message = payload.get("ErrorMessage") or _(
                    "Generation failed. Review your prompt and output format."
                )
                settings_inner.last_error = error_message
                logger.error("Job %s failed: %s", job_id, error_message)
                self._restore_cursor()
                self._active_job = None
                return None

            return POLL_INTERVAL

        bpy.app.timers.register(poll_job, first_interval=POLL_INTERVAL)
        return {'FINISHED'}


_CLASSES = (MH3D_OT_OpenAPILink, MH3D_OT_Generate)


def register() -> None:
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    logger.info("Operators registered.")


def unregister() -> None:
    for cls in reversed(_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
    logger.info("Operators unregistered.")
