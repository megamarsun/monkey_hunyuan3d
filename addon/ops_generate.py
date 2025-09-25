# -*- coding: utf-8 -*-
"""Operators for interacting with the Hunyuan3D API."""

from __future__ import annotations

import base64
import binascii
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

from . import DEFAULT_REGION, get_logger

logger = get_logger()

API_ENDPOINT = "ai3d.tencentcloudapi.com"
API_VERSION = "2025-05-13"
POLL_SCHEDULE = (2.0, 3.0, 5.0, 8.0, 13.0, 15.0)


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
    except ImportError as exc:  # pragma: no cover - depends on user environment
        raise RuntimeError(
            _(
                "SDK not installed: run 'pip install tencentcloud-sdk-python' in Blender's Python."
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


@dataclass
class _ImageBundle:
    values: list[str]
    source: str
    multi: bool
    as_base64: bool
    total_bytes: Optional[int] = None
    base64_bytes: Optional[int] = None


def _clean_base64(value: str) -> str:
    stripped = value.strip()
    if stripped.startswith("data:") and "," in stripped:
        stripped = stripped.split(",", 1)[1]
    return stripped


def _validate_base64(value: str) -> tuple[str, int, int]:
    cleaned = _clean_base64(value)
    try:
        decoded = base64.b64decode(cleaned, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(_("Invalid base64 image payload: {error}").format(error=exc)) from exc
    return cleaned, len(decoded), len(cleaned)


def _allowed_extensions() -> set[str]:
    return {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def _load_image_bytes(path: str) -> bytes:
    try:
        from PIL import Image  # type: ignore[import]
    except Exception:  # pragma: no cover - optional dependency
        with open(path, "rb") as handle:
            return handle.read()

    try:
        with Image.open(path) as image:
            has_alpha = image.mode in {"RGBA", "LA"}
            target_mode = "RGBA" if has_alpha else "RGB"
            converted = image.convert(target_mode)
            buffer = io.BytesIO()
            if has_alpha:
                converted.save(buffer, format="PNG", optimize=True)
            else:
                converted.save(buffer, format="JPEG", optimize=True, quality=92)
            return buffer.getvalue()
    except Exception as exc:  # pragma: no cover - depends on Pillow support
        logger.warning("Failed to process image %s via Pillow: %s", path, exc)
        with open(path, "rb") as handle:
            return handle.read()


def _encode_file_to_base64(path: str) -> tuple[str, int, int]:
    data = _load_image_bytes(path)
    encoded = base64.b64encode(data).decode("ascii")
    return encoded, len(data), len(encoded)


def _prepare_images(settings: bpy.types.PropertyGroup) -> Optional[_ImageBundle]:
    requires_image = settings.input_mode in {"IMAGE", "TEXT_IMAGE"}
    if not requires_image:
        return None

    source = settings.image_source
    multi = bool(settings.multi_view)

    if source == 'URL':
        if multi:
            values = [item.value.strip() for item in settings.image_files if item.value.strip()]
        else:
            url = settings.image_url.strip()
            values = [url] if url else []
        if not values:
            raise ValueError(_("No image URLs provided."))
        for value in values:
            lower = value.lower()
            if not (lower.startswith("http://") or lower.startswith("https://")):
                raise ValueError(_("Image URLs must start with http:// or https://."))
        return _ImageBundle(values=values, source='URL', multi=multi, as_base64=False)

    if source == 'BASE64':
        if multi:
            raw_values = [item.value for item in settings.image_files if item.value.strip()]
        else:
            base_value = settings.image_b64.strip()
            raw_values = [base_value] if base_value else []
        if not raw_values:
            raise ValueError(_("No base64 images were provided."))
        cleaned_values: list[str] = []
        total_bytes = 0
        total_encoded = 0
        for raw in raw_values:
            cleaned, decoded_bytes, encoded_bytes = _validate_base64(raw)
            cleaned_values.append(cleaned)
            total_bytes += decoded_bytes
            total_encoded += encoded_bytes
        limit_mb = max(1, int(getattr(settings, "image_b64_limit_mb", 20)))
        limit_bytes = limit_mb * 1024 * 1024
        if total_bytes > limit_bytes:
            raise ValueError(
                _("Total decoded base64 size {size:.1f} MB exceeds limit of {limit} MB.").format(
                    size=total_bytes / (1024 * 1024),
                    limit=limit_mb,
                )
            )
        return _ImageBundle(
            values=cleaned_values,
            source='BASE64',
            multi=multi,
            as_base64=True,
            total_bytes=total_bytes,
            base64_bytes=total_encoded,
        )

    # FILE source
    items = [item for item in settings.image_files if item.value.strip()]
    if not items:
        raise ValueError(_("No image files were selected."))
    if not multi:
        index = getattr(settings, "image_files_index", 0)
        if 0 <= index < len(items):
            items = [items[index]]
        else:
            items = [items[-1]]
    encoded_values: list[str] = []
    total_bytes = 0
    total_encoded = 0
    for entry in items:
        original = entry.value
        path_value = bpy.path.abspath(original) if hasattr(bpy, "path") else original
        path_value = os.path.expanduser(path_value)
        if not os.path.isfile(path_value):
            raise ValueError(_("Image file not found: {path}").format(path=path_value))
        ext = os.path.splitext(path_value)[1].lower()
        if ext and ext not in _allowed_extensions():
            raise ValueError(
                _("Unsupported image file extension: {extension}").format(extension=ext)
            )
        encoded, decoded_bytes, encoded_bytes = _encode_file_to_base64(path_value)
        encoded_values.append(encoded)
        total_bytes += decoded_bytes
        total_encoded += encoded_bytes
    return _ImageBundle(
        values=encoded_values,
        source='FILE',
        multi=multi,
        as_base64=True,
        total_bytes=total_bytes,
        base64_bytes=total_encoded,
    )


def _build_payload(
    settings: bpy.types.PropertyGroup,
    prompt: str,
    images: Optional[_ImageBundle],
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "ResultFormat": settings.result_format,
    }
    if prompt:
        payload["Prompt"] = prompt
    if getattr(settings, "enable_pbr", False):
        payload["EnablePBR"] = True
    if getattr(settings, "front_mask", False):
        payload["FrontMask"] = True
    if images:
        key = "Images" if images.multi else "Image"
        payload[key] = images.values if images.multi else images.values[0]
    return payload


def _summarize_request(
    settings: bpy.types.PropertyGroup,
    images: Optional[_ImageBundle],
) -> str:
    parts = [f"input={settings.input_mode}"]
    parts.append(f"api={settings.api_target}")
    if images:
        parts.append(f"source={settings.image_source}")
        parts.append(f"images={len(images.values)}")
        if images.total_bytes:
            mb = images.total_bytes / (1024 * 1024)
            parts.append(f"total≈{mb:.1f}MB")
    return " / ".join(parts)


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
        secret_id = os.environ.get("TENCENTCLOUD_SECRET_ID") or settings.secret_id.strip()
        secret_key = os.environ.get("TENCENTCLOUD_SECRET_KEY") or settings.secret_key.strip()
        return secret_id, secret_key

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

        prompt_raw = settings.prompt.strip()
        prompt_required = settings.input_mode in {"TEXT", "TEXT_IMAGE"}
        if prompt_required and not prompt_raw:
            message = _("Prompt is required for the selected input mode.")
            settings.last_status = "ERROR"
            settings.last_error = message
            self.report({'ERROR'}, message)
            logger.error(message)
            return {'CANCELLED'}

        try:
            images_bundle = _prepare_images(settings)
        except ValueError as exc:
            message = str(exc)
            settings.last_status = "ERROR"
            settings.last_error = message
            self.report({'ERROR'}, message)
            logger.error("Image preparation failed: %s", exc)
            return {'CANCELLED'}

        if settings.input_mode in {"IMAGE", "TEXT_IMAGE"} and images_bundle is None:
            message = _("At least one reference image is required.")
            settings.last_status = "ERROR"
            settings.last_error = message
            self.report({'ERROR'}, message)
            logger.error(message)
            return {'CANCELLED'}

        prompt_value = prompt_raw if settings.input_mode != "IMAGE" else ""
        payload = _build_payload(settings, prompt_value, images_bundle)
        settings.last_request_summary = _summarize_request(settings, images_bundle)

        target = settings.api_target
        if target != "TENCENT_CLOUD":
            message = _(
                "API target '{target}' is not implemented yet."
            ).format(target=target)
            settings.last_status = "ERROR"
            settings.last_error = message
            self.report({'ERROR'}, message)
            logger.error(message)
            return {'CANCELLED'}

        try:
            bundle = _import_sdk()
        except RuntimeError as exc:
            self.report({'ERROR'}, str(exc))
            logger.error(str(exc))
            return {'CANCELLED'}

        secret_id, secret_key = self._resolve_credentials(settings)
        if not secret_id or not secret_key:
            message = _(
                "API keys missing: set environment variables or fill SecretId/SecretKey."
            )
            settings.last_status = "ERROR"
            settings.last_error = message
            self.report({'ERROR'}, message)
            logger.error(message)
            return {'CANCELLED'}

        settings.last_error = ""
        settings.last_status = "SUBMITTING"
        settings.job_id = ""

        region = settings.region or DEFAULT_REGION
        client = _create_client(bundle, secret_id, secret_key, region)
        params: Dict[str, Any] = dict(payload)
        reenable_pbr_after_success = not settings.enable_pbr

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

        poll_attempt = 1

        def poll_job() -> Optional[float]:
            nonlocal poll_attempt
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
                interval = POLL_SCHEDULE[min(poll_attempt, len(POLL_SCHEDULE) - 1)]
                poll_attempt += 1
                return interval
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

            interval = POLL_SCHEDULE[min(poll_attempt, len(POLL_SCHEDULE) - 1)]
            poll_attempt += 1
            return interval

        bpy.app.timers.register(poll_job, first_interval=POLL_SCHEDULE[0])
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
