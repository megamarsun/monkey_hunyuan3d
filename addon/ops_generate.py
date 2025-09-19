# -*- coding: utf-8 -*-
"""Operators for interacting with the Hunyuan3D API."""

from __future__ import annotations

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
POLL_INTERVAL = 2.0


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
    client_profile = bundle.client_profile_cls(httpProfile=http_profile)
    cred = bundle.credential_factory(secret_id, secret_key)
    region_value = (region or DEFAULT_REGION).strip() or DEFAULT_REGION
    return bundle.client_cls(cred, region_value, client_profile)


def _download_file(url: str, suffix: str) -> str:
    tmp = tempfile.NamedTemporaryFile(prefix="mh3d_", suffix=suffix, delete=False)
    tmp_path = tmp.name
    tmp.close()
    try:
        with urllib.request.urlopen(url) as response, open(tmp_path, "wb") as handle:
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

        prompt = settings.prompt.strip()
        if not prompt:
            message = _("Prompt is empty.")
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
                "API keys missing: configure environment variables or fill SecretId/SecretKey in the panel."
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
            "Prompt": prompt,
            "ResultFormat": settings.result_format,
        }
        if settings.enable_pbr:
            params["EnablePBR"] = True

        self._set_wait_cursor(context)
        try:
            response_raw = client.call("SubmitHunyuanTo3DJob", params)
            response = json.loads(response_raw).get("Response", {})
            job_id = response.get("JobId")
            if not job_id:
                raise ValueError("JobId missing in response.")
        except bundle.exception_cls as exc:  # type: ignore[attr-defined]
            message = _("API error during submission: {error}").format(error=str(exc))
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

        info_message = _("Job submitted. Tracking progress in the status panel.")
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
            except bundle.exception_cls as exc:  # type: ignore[attr-defined]
                message_inner = _("API error while querying job: {error}").format(error=str(exc))
                settings_inner.last_status = "ERROR"
                settings_inner.last_error = message_inner
                logger.error("Query failed for job %s: %s", job_id, exc)
                self._restore_cursor()
                self._active_job = None
                return None
            except Exception as exc:  # pragma: no cover - depends on network state
                message_inner = _("Network error while querying job: {error}").format(error=exc)
                settings_inner.last_status = "ERROR"
                settings_inner.last_error = message_inner
                logger.error("Query failed for job %s: %s", job_id, exc)
                self._restore_cursor()
                self._active_job = None
                return None

            status = payload.get("Status") or payload.get("JobStatus") or ""
            settings_inner.last_status = status or "UNKNOWN"

            if (
                status in {"QUEUED", "QUEUING", "PROCESSING", "RUNNING", "PENDING"}
                or not status
            ):
                return POLL_INTERVAL
            if status in {"DONE", "SUCCEED", "SUCCEEDED", "SUCCESS"}:
                files = payload.get("ResultFile3Ds") or []
                url = None
                if files:
                    url = files[0].get("Url") or files[0].get("URL")
                if not url:
                    settings_inner.last_error = _("No download URL returned by the service.")
                    settings_inner.last_status = "ERROR"
                    logger.error("Job %s completed but returned no URL.", job_id)
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
                except urllib.error.URLError as exc:
                    message_inner = _("Network error while downloading file: {error}").format(error=exc)
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
            if status in {"FAIL", "FAILED"}:
                error_message = payload.get("ErrorMessage") or _(
                    "Generation failed. Review your prompt and output format."
                )
                settings_inner.last_error = error_message
                logger.error("Job %s failed: %s", job_id, error_message)
                self._restore_cursor()
                self._active_job = None
                return None

            self._restore_cursor()
            self._active_job = None
            return None

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
