# -*- coding: utf-8 -*-
# monkey_hunyuan3d/__init__.py

bl_info = {
    "name": "Monkey Hunyuan3D (Mock UI)",
    "author": "Sakaki Masamune",
    "version": (0, 0, 5),
    "blender": (4, 0, 0),  # 最低バージョンを 4.0 に下げて検出漏れを防ぐ
    "location": "3D View > Sidebar > Monkey Hunyuan3D",
    "description": "UIだけ表示するモック。強制ログ＋タイマー。読み込み例外を必ず表示。",
    "category": "3D View",
}

import bpy
import sys, logging, traceback

PKG_NAME = __package__ or "monkey_hunyuan3d"

# ---- 強制ログ（Blenderのコンソール/ターミナルに必ず出す）----
_logger = logging.getLogger(PKG_NAME)
if not _logger.handlers:
    h = logging.StreamHandler(stream=sys.stdout)
    h.setFormatter(logging.Formatter("[MonkeyHunyuan3D] %(levelname)s: %(message)s"))
    _logger.addHandler(h)
_logger.setLevel(logging.INFO)
_logger.info("Importing package: %s  v%s", PKG_NAME, ".".join(map(str, bl_info["version"])))

# ---- ダミーパネル（core読み込みに失敗しても登録だけは通す）----
class MONKEYHUNYUAN3D_PT_dummy(bpy.types.Panel):
    bl_label = "Monkey Hunyuan3D (Dummy)"
    bl_idname = "MONKEYHUNYUAN3D_PT_dummy"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Monkey Hunyuan3D"

    def draw(self, context):
        col = self.layout.column(align=True)
        col.label(text="Core not loaded yet (dummy panel).")
        col.operator("monkey_hunyuan3d._load_core_now", icon="FILE_REFRESH")
        col.separator()
        col.label(text="If you see this panel, add-on IS registered.")
        col.label(text="Next: press the button to load core.py")

class MONKEYHUNYUAN3D_OT__load_core_now(bpy.types.Operator):
    bl_idname = "monkey_hunyuan3d._load_core_now"
    bl_label = "Load Core Now"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        try:
            from . import core
            core.register()
            # ダミーパネルは以後不要なので隠す
            try:
                bpy.utils.unregister_class(MONKEYHUNYUAN3D_PT_dummy)
            except Exception:
                pass
            self.report({'INFO'}, "core.py loaded and registered.")
            _logger.info("core.py loaded and registered.")
        except Exception as e:
            msg = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            _logger.error("core import/register failed:\n%s", msg)
            self.report({'ERROR'}, "Core load failed (see console).")
        return {'FINISHED'}

_DUMMY_CLASSES = (MONKEYHUNYUAN3D_PT_dummy, MONKEYHUNYUAN3D_OT__load_core_now)

def register():
    # 1) とりあえずダミーを登録（これが見えれば「登録は成功」）
    for c in _DUMMY_CLASSES:
        bpy.utils.register_class(c)
    _logger.info("Addon base registered. Trying to load core...")
    # 2) コア登録を試行（失敗してもアドオン自体は有効化された状態を保つ）
    try:
        from . import core
        core.register()
        # コアに置き換わったのでダミーを外す
        for c in reversed(_DUMMY_CLASSES):
            try:
                bpy.utils.unregister_class(c)
            except Exception:
                pass
        _logger.info("Core registered successfully.")
    except Exception as e:
        msg = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        _logger.error("core import/register failed (but addon stays enabled):\n%s", msg)

def unregister():
    # core 側の unregister を呼べるなら呼ぶ
    try:
        from . import core
        core.unregister()
    except Exception:
        pass
    # ダミーを安全に外す
    for c in reversed(_DUMMY_CLASSES):
        try:
            bpy.utils.unregister_class(c)
        except Exception:
            pass
    _logger.info("Addon unregistered.")
