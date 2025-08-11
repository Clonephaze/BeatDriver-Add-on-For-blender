import os
import bpy


class BeatDriver_Panel_UI(bpy.types.Panel):
    bl_label = "BeatDriver"
    bl_idname = "BEATDRIVER_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BeatDriver"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Header
        layout.label(text="Welcome to BeatDriver!")

        # If audio selected, show button with song name, otherwise generic label + button
        if scene.beatdriver_audio_path:
            song = os.path.basename(scene.beatdriver_audio_path)
            layout.label(text="Selected audio")
            # Button still opens file selector; we override the label to include the filename
            layout.operator(
                "beatdriver.select_audio",
                icon="FILE_SOUND",
                text=f'Select Audio File ("{song}")',
            )
        else:
            layout.label(text="Import your audio below:")
            layout.operator(
                "beatdriver.select_audio", icon="FILE_SOUND", text="Select Audio File"
            )

        # If audio selected show fps and build button
        if scene.beatdriver_audio_path:
            layout.prop(scene, "beatdriver_fps")
            layout.operator("beatdriver.build", text="Build BeatDriver (Might Lag)")

        # After build: show status rows
        if getattr(scene, "beatdriver_built", False):
            layout.separator()
            layout.label(text="BeatDriver status:")
            box = layout.box()
            box_row = box.row()
            box_row.label(
                text=f"Playback synced to audio: {'✓' if scene.beatdriver_sync else '✗'}"
            )
            box_row = box.row()
            box_row.label(
                text=f"Audio added to video Sequencer: {'✓' if scene.beatdriver_in_vse else '✗'}"
            )
            box_row = box.row()
            box_row.label(
                text=f"Playback End frame count set to {scene.beatdriver_end_frame}"
            )
            box_row = box.row()
            box_row.label(
                text=f"Object created with BeatDriver node: {scene.beatdriver_object_name}"
            )


def register():
    bpy.utils.register_class(BeatDriver_Panel_UI)


def unregister():
    bpy.utils.unregister_class(BeatDriver_Panel_UI)
