# -*- coding: utf-8 -*-
"""Utilities for managing third-party dependencies in a vendor directory."""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
from typing import Optional

VENDOR_DIR = os.path.join(os.path.dirname(__file__), "vendor")


def _ensure_vendor_path() -> None:
    """Ensure the vendor directory is at the front of ``sys.path``."""
    if VENDOR_DIR not in sys.path:
        sys.path.insert(0, VENDOR_DIR)


def ensure_package(mod_name: str, pip_name: Optional[str] = None, version: Optional[str] = None) -> None:
    """Ensure *mod_name* can be imported, installing it into ``vendor/`` if needed."""
    _ensure_vendor_path()
    try:
        importlib.import_module(mod_name)
        return
    except Exception:
        pass

    package = pip_name or mod_name
    if version:
        package = f"{package}=={version}"

    args = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--no-cache-dir",
        "--target",
        VENDOR_DIR,
        package,
    ]

    subprocess.check_call(args)
    importlib.invalidate_caches()
    _ensure_vendor_path()
    importlib.import_module(mod_name)
