import bpy

class BEATDRIVER_PT_panel(bpy.types.Panel):
    bl_label = "BeatDriver"
    bl_idname = "BEATDRIVER_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BeatDriver"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text="Welcome to BeatDriver!")
        layout.label(text="Import your audio below:")
        layout.operator("beatdriver.select_audio", icon="FILE_SOUND")

        if scene.beatdriver_audio_path:
            layout.prop(scene, "beatdriver_fps")
            layout.operator("beatdriver.build", text="Build BeatDriver")

# Registration
classes = [BEATDRIVER_PT_panel]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
