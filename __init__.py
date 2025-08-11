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
from bpy.props import StringProperty, IntProperty, BoolProperty

# Module imports
from . import operators, ui


# === Properties ===
def register_props():
    bpy.types.Scene.beatdriver_audio_path = StringProperty(
        name="Audio File Path", default="", subtype="FILE_PATH"
    )
    bpy.types.Scene.beatdriver_fps = IntProperty(
        name="Scene FPS",
        default=30,
        min=1,
        max=240,
        update=lambda self, ctx: setattr(ctx.scene.render, "fps", self.beatdriver_fps),
    )
    bpy.types.Scene.beatdriver_built = BoolProperty(
        name="BeatDriver Built", default=False
    )
    bpy.types.Scene.beatdriver_sync = BoolProperty(
        name="Playback Synced", default=False
    )
    bpy.types.Scene.beatdriver_in_vse = BoolProperty(name="In VSE", default=False)
    bpy.types.Scene.beatdriver_end_frame = IntProperty(
        name="BeatDriver End Frame", default=0
    )
    bpy.types.Scene.beatdriver_object_name = StringProperty(
        name="BeatDriver Object", default=""
    )
    bpy.types.Scene.beatdriver_last_error = StringProperty(
        name="BeatDriver Last Error", default=""
    )


def unregister_props():
    del bpy.types.Scene.beatdriver_audio_path
    del bpy.types.Scene.beatdriver_fps
    del bpy.types.Scene.beatdriver_built
    del bpy.types.Scene.beatdriver_sync
    del bpy.types.Scene.beatdriver_in_vse
    del bpy.types.Scene.beatdriver_end_frame
    del bpy.types.Scene.beatdriver_object_name
    del bpy.types.Scene.beatdriver_last_error


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
