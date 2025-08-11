import os
import shutil
import subprocess
import bpy


class BEATDRIVER_OT_select_audio(bpy.types.Operator):
    bl_idname = "beatdriver.select_audio"
    bl_label = "Select Audio File"
    bl_description = "Select an audio file to import"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        context.scene.beatdriver_audio_path = self.filepath
        self.report({"INFO"}, f"Selected audio: {self.filepath}")
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


class BEATDRIVER_OT_build(bpy.types.Operator):
    bl_idname = "beatdriver.build"
    bl_label = "Build BeatDriver"
    bl_description = "Create the BeatDriver setup from selected audio"

    def execute(self, context):
        scene = context.scene
        audio_path = scene.beatdriver_audio_path

        if not audio_path or not os.path.exists(audio_path):
            self.report({"ERROR"}, "No valid audio file selected")
            return {"CANCELLED"}

        if not bpy.data.filepath:
            self.report({"ERROR"}, "Please save your Blender project first.")
            return {"CANCELLED"}

        project_dir = os.path.dirname(bpy.data.filepath)
        song_name = os.path.splitext(os.path.basename(audio_path))[0]

        scene.sync_mode = "AUDIO_SYNC"

        dest_audio_path = os.path.join(project_dir, os.path.basename(audio_path))
        if audio_path != dest_audio_path:
            shutil.copy2(audio_path, dest_audio_path)

        if not scene.sequence_editor:
            scene.sequence_editor_create()

        scene.sequence_editor.sequences.new_sound(
            name=os.path.basename(dest_audio_path),
            filepath=dest_audio_path,
            channel=1,
            frame_start=1,
        )

        addon_dir = os.path.dirname(__file__)
        blend_path = os.path.join(addon_dir, "BeatDriver.blend")

        PARENT_GROUP_NAME = "BeatDriverParent"
        # Create unique name for this song's node group
        unique_group_name = f"BeatDriver_{song_name}"

        # Check if we already have a unique group for this song
        existing_group = bpy.data.node_groups.get(unique_group_name)
        if existing_group:
            node_group = existing_group
        else:
            # Append the parent GN setup from the .blend
            with bpy.data.libraries.load(blend_path, link=False) as (
                data_from,
                data_to,
            ):
                if PARENT_GROUP_NAME in data_from.node_groups:
                    data_to.node_groups = [PARENT_GROUP_NAME]
                else:
                    self.report(
                        {"ERROR"}, f"{PARENT_GROUP_NAME} not found in BeatDriver.blend"
                    )
                    return {"CANCELLED"}

            # Get the loaded node group
            source_group = bpy.data.node_groups.get(PARENT_GROUP_NAME)
            if not source_group:
                self.report({"ERROR"}, f"Failed to load {PARENT_GROUP_NAME}")
                return {"CANCELLED"}

            # Create a copy with unique name
            node_group = source_group.copy()
            node_group.name = unique_group_name

            # Remove the original imported group to keep things clean
            bpy.data.node_groups.remove(source_group)

        # Create mesh object for the GN modifier
        empty_name = f"BeatDriver - {song_name}"
        mesh = bpy.data.meshes.new(empty_name)
        empty_obj = bpy.data.objects.new(empty_name, mesh)
        scene.collection.objects.link(empty_obj)

        # Run external analysis script
        csv_name = f"{song_name}.csv"
        csv_path = os.path.join(project_dir, csv_name)
        fps = scene.beatdriver_fps
        script_path = os.path.join(addon_dir, "audio_analysis.py")

        subprocess.run(
            ["python", script_path, dest_audio_path, csv_path, str(fps)], check=True
        )

        # Set Path to CSV in modifier
        rel_csv_path = f"//{csv_name}"

        # Add GN modifier and assign the unique node group
        gn_mod = empty_obj.modifiers.new(name="BeatDriver", type="NODES")
        gn_mod.node_group = node_group

        # Set Path to CSV in the node group input
        group_input_node = node_group.nodes.get("Group")
        if group_input_node:
            group_input_node.inputs[0].default_value = rel_csv_path
        else:
            self.report({"WARNING"}, "Group input node not found in node group")

        self.report({"INFO"}, f"BeatDriver setup complete for {song_name}")

        # Count lines in CSV and set scene frame_end
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                num_lines = sum(1 for _ in f)
            scene.frame_end = num_lines
        except Exception as e:
            self.report({"WARNING"}, f"Could not set frame_end from CSV: {e}")
        return {"FINISHED"}


# Registration
classes = [BEATDRIVER_OT_select_audio, BEATDRIVER_OT_build]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
