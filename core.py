# -*- coding: utf-8 -*-
# monkey_hunyuan3d/core.py

import sys, logging, bpy
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty

PKG_NAME = __package__ or "monkey_hunyuan3d"

# 強制ログ
logger = logging.getLogger(PKG_NAME)
if not logger.handlers:
    import sys as _sys, logging as _logging
    h = _logging.StreamHandler(stream=_sys.stdout)
    h.setFormatter(_logging.Formatter("[MonkeyHunyuan3D] %(levelname)s: %(message)s"))
    logger.addHandler(h)
logger.setLevel(logging.INFO)
logger.info("core.py importing...")

# ---- AddonPreferences ----
class MONKEYHUNYUAN3D_AddonPreferences(bpy.types.AddonPreferences):
    # ここは *実際のモジュール名* に一致させる。Zipのトップフォルダ名が変わるとズレるので注意
    bl_idname = "monkey_hunyuan3d"

    api_key: StringProperty(
        name="API Key", subtype='PASSWORD',
        description="（モック）実通信はしません。"
    )
    endpoint: StringProperty(
        name="Endpoint",
        default="https://api.example.com/hunyuan3d",
        description="（モック）UI表示のみ。"
    )
    def draw(self, context):
        box = self.layout.box()
        box.label(text="Monkey Hunyuan3D Preferences (Mock)")
        box.prop(self, "api_key")
        box.prop(self, "endpoint")

# ---- Scene Properties ----
def _enum_models(self, context):
    return [
        ("HY3D-FAST", "HY3D-FAST", "（モック）高速"),
        ("HY3D-STD",  "HY3D-STD",  "（モック）標準"),
        ("HY3D-HQ",   "HY3D-HQ",   "（モック）高品質"),
    ]

def define_scene_props():
    bpy.types.Scene.mh3d_prompt = StringProperty(
        name="Prompt", default="a cute glass creature"
    )
    bpy.types.Scene.mh3d_seed = IntProperty(
        name="Seed", min=0, max=2**31-1, default=0
    )
    bpy.types.Scene.mh3d_model = EnumProperty(
        name="Model", items=_enum_models, default="HY3D-STD"
    )
    bpy.types.Scene.mh3d_timer_pin = BoolProperty(
        name="Heartbeat Timer", default=False, description="モックのハートビート"
    )

def clear_scene_props():
    for k in ("mh3d_prompt", "mh3d_seed", "mh3d_model", "mh3d_timer_pin"):
        if hasattr(bpy.types.Scene, k):
            delattr(bpy.types.Scene, k)

# ---- Operators ----
class MONKEYHUNYUAN3D_OT_generate_mock(bpy.types.Operator):
    bl_idname = "monkey_hunyuan3d.generate_mock"
    bl_label  = "Generate (Mock)"
    bl_options = {'REGISTER'}

    def execute(self, context):
        s = context.scene
        self.report({'INFO'}, f"Mock call: model={s.mh3d_model}, seed={s.mh3d_seed}")
        logger.info("Mock generate | model=%s seed=%d prompt=%r",
                    s.mh3d_model, s.mh3d_seed, s.mh3d_prompt)
        return {'FINISHED'}

# ---- Panel ----
class MONKEYHUNYUAN3D_PT_panel(bpy.types.Panel):
    bl_label = "Monkey Hunyuan3D (Mock)"
    bl_idname = "MONKEYHUNYUAN3D_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Monkey Hunyuan3D"

    def draw(self, context):
        layout = self.layout
        s = context.scene

        # Prefs をインライン表示
        addon = context.preferences.addons.get("monkey_hunyuan3d")
        if addon:
            prefs = addon.preferences
            box = layout.box()
            box.label(text="Preferences")
            box.prop(prefs, "api_key", text="API Key")
            box.prop(prefs, "endpoint", text="Endpoint")

        box = layout.box()
        box.label(text="Parameters (Mock)")
        box.prop(s, "mh3d_model")
        box.prop(s, "mh3d_prompt")
        box.prop(s, "mh3d_seed")
        layout.operator("monkey_hunyuan3d.generate_mock", icon="PLAY")

# ---- Registration ----
_CLASSES = (
    MONKEYHUNYUAN3D_AddonPreferences,
    MONKEYHUNYUAN3D_OT_generate_mock,
    MONKEYHUNYUAN3D_PT_panel,
)

def register():
    logger.info("core.register()")
    for c in _CLASSES:
        bpy.utils.register_class(c)
    define_scene_props()
    logger.info("core registered OK. Nパネル『Monkey Hunyuan3D』を確認してください。")

def unregister():
    logger.info("core.unregister()")
    clear_scene_props()
    for c in reversed(_CLASSES):
        try:
            bpy.utils.unregister_class(c)
        except Exception:
            pass
    logger.info("core unregistered.")
