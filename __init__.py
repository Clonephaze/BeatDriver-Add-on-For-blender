bl_info = {
    "name": "BeatDriver",
    "author": "Clonephaze",
    "version": (0, 0, 1),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > BeatDriver",
    "description": "Imports audio, generates CSV, and sets up GN audio driver",
    "category": "Animation",
}

import importlib
import bpy
from bpy.props import StringProperty, IntProperty

# Local imports
from . import operators, ui

# Reload during development
for mod in (operators, ui):
    importlib.reload(mod)

# === Properties ===
def register_props():
    bpy.types.Scene.beatdriver_audio_path = StringProperty(
        name="Audio File Path",
        default="",
        subtype='FILE_PATH'
    )
    bpy.types.Scene.beatdriver_fps = IntProperty(
        name="Scene FPS",
        default=30,
        min=1,
        max=240,
        update=lambda self, ctx: setattr(ctx.scene.render, "fps", self.beatdriver_fps)
    )

def unregister_props():
    del bpy.types.Scene.beatdriver_audio_path
    del bpy.types.Scene.beatdriver_fps

# === Register / Unregister ===
def register():
    register_props()
    operators.register()
    ui.register()

def unregister():
    ui.unregister()
    operators.unregister()
    unregister_props()

if __name__ == "__main__":
    register()
