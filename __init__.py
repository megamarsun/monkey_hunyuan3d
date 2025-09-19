# -*- coding: utf-8 -*-
"""Entry point for the Monkey hunyuan3D Blender add-on."""

from __future__ import annotations

from .addon import bl_info  # noqa: F401
from .addon import register as register  # re-export
from .addon import unregister as unregister  # re-export

__all__ = ("bl_info", "register", "unregister")
