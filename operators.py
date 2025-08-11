import os
import shutil
import subprocess
import bpy


class Select_Audio(bpy.types.Operator):
    bl_idname = "beatdriver.select_audio"
    bl_label = "Select Audio File"
    bl_description = "Select an audio file to import"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(
        default="*.mp3;*.wav;*.ogg;*.flac", options={"HIDDEN"}
    )

    def execute(self, context):
        """
        Main execution method for the Select Audio operator.
        Sets the audio file path in the scene properties and initializes BeatDriver state.
        """
        context.scene.beatdriver_audio_path = self.filepath
        context.scene.beatdriver_built = False
        context.scene.beatdriver_sync = False
        context.scene.beatdriver_in_vse = False
        context.scene.beatdriver_end_frame = 0
        context.scene.beatdriver_object_name = ""
        context.scene.beatdriver_last_error = ""
        self.report({"INFO"}, f"Selected audio: {self.filepath}")

        # Get and set the user's current fps
        user_fps = context.scene.render.fps
        setattr(context.scene, "beatdriver_fps", user_fps)
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


class Build_BeatDriver(bpy.types.Operator):
    """
    Builds the BeatDriver setup from the selected audio file using a sequential execution method.
    """

    bl_idname = "beatdriver.build"
    bl_label = "Build BeatDriver"
    bl_description = "Create the BeatDriver setup from selected audio. The first run may need to download additional libraries to run."

    def execute(self, context):
        """
        Main execution method for the BeatDriver operator.
        """
        scene = context.scene

        # Validate save state and audio existence
        if not self._validate_prerequisites(scene):
            return {"CANCELLED"}

        # Set dictionary with needed paths and configurations
        project_config = self._get_project_configuration(scene)

        # Set up the audio in the sequencer and configure scene settings
        self._setup_audio_sequencer(scene, project_config)

        # Creates a copy of the BeatDriver node group for the specific song
        node_group = self._setup_node_group(project_config)
        if not node_group:
            return {"CANCELLED"}

        # Create the object that will hold the geometry nodes modifier
        empty_obj = self._create_beatdriver_object(scene, project_config)

        # Runs external audio analysis tool
        if not self._run_audio_analysis(project_config):
            return {"CANCELLED"}

        # Sets the settings for the specific song's BeatDriver geo node
        self._setup_geometry_nodes_modifier(empty_obj, node_group, project_config)

        # Sets max framecount to the frame count of the audio, to avoid premauture audio cutoff
        self._configure_timeline(scene, project_config)

        scene.beatdriver_last_error = ""
        scene.beatdriver_built = True

        self.report(
            {"INFO"}, f"BeatDriver setup complete for {project_config['song_name']}"
        )
        return {"FINISHED"}

    def _validate_prerequisites(self, scene):
        """
        Validate all prerequisites before building BeatDriver.

        Args:
            scene: The current Blender scene

        Returns:
            bool: True if all prerequisites are met, False otherwise
        """
        audio_path = scene.beatdriver_audio_path

        # Check if audio file exists
        if not audio_path or not os.path.exists(audio_path):
            self.report({"ERROR"}, "No valid audio file selected")
            return False

        # Check if Blender project is saved
        if not bpy.data.filepath:
            self.report({"ERROR"}, "Please save your Blender project first.")
            return False

        return True

    def _get_project_configuration(self, scene):
        """
        Prepare project configuration data.

        Args:
            scene: The current Blender scene

        Returns:
            dict: Configuration dictionary containing paths and names:
                - audio_path: Path to the audio file
                - project_dir: Directory of the Blender project
                - song_name: Name of the song (without extension)
                - dest_audio_path: Destination path for the audio file copy
                - csv_name: Name of the CSV file
                - csv_path: Path to the CSV file
                - fps: Frames per second setting
                - unique_group_name: Unique name for the node group
                - empty_name: Name for the empty object
        """
        audio_path = scene.beatdriver_audio_path
        project_dir = os.path.dirname(bpy.data.filepath)
        song_name = os.path.splitext(os.path.basename(audio_path))[0]

        return {
            "audio_path": audio_path,
            "project_dir": project_dir,
            "song_name": song_name,
            "dest_audio_path": os.path.join(project_dir, os.path.basename(audio_path)),
            "csv_name": f"{song_name}.csv",
            "csv_path": os.path.join(project_dir, f"{song_name}.csv"),
            "fps": scene.beatdriver_fps,
            "unique_group_name": f"BeatDriver_{song_name}",
            "empty_name": f"BeatDriver - {song_name}",
        }

    def _setup_audio_sequencer(self, scene, config):
        """
        Sets the audio to track 1 in Blender's video sequencer, and sets the scene to sync the playback to the audio to ensure proper timing.

        Args:
            scene: The current Blender scene
            config: Project configuration dictionary
        """
        # Set sync mode to audio to avoid timing issues
        scene.sync_mode = "AUDIO_SYNC"
        scene.beatdriver_sync = True

        # Copy audio file to project directory
        if config["audio_path"] != config["dest_audio_path"]:
            shutil.copy2(config["audio_path"], config["dest_audio_path"])

        # Create sequence editor if it doesn't exist - Haven't encountered this but better safe than sorry
        if not scene.sequence_editor:
            scene.sequence_editor_create()

        # Add audio strip to sequencer in first channel
        scene.sequence_editor.sequences.new_sound(
            name=os.path.basename(config["dest_audio_path"]),
            filepath=config["dest_audio_path"],
            channel=1,
            frame_start=1,
        )
        scene.beatdriver_in_vse = True

    def _setup_node_group(self, config):
        """
        Create a unique geometry node group for the selected song.

        Args:
            config: Project configuration dictionary

        Returns:
            NodeGroup: The node group for this BeatDriver instance, or None if failed
        """
        PARENT_GROUP_NAME = "BeatDriverParent"

        # Check if we already have a unique group for this song
        existing_group = bpy.data.node_groups.get(config["unique_group_name"])
        if existing_group:
            return existing_group

        # Load node group that contains the BeatDriver node group
        addon_dir = os.path.dirname(__file__)
        blend_path = os.path.join(addon_dir, "BeatDriver.blend")
        with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
            if PARENT_GROUP_NAME in data_from.node_groups:
                data_to.node_groups = [PARENT_GROUP_NAME]
            else:
                self.report(
                    {"ERROR"}, f"{PARENT_GROUP_NAME} not found in BeatDriver.blend"
                )
                return None

        # Get the loaded node group
        source_group = bpy.data.node_groups.get(PARENT_GROUP_NAME)
        if not source_group:
            self.report({"ERROR"}, f"Failed to load {PARENT_GROUP_NAME}")
            return None

        # Create a copy with unique name for this song
        node_group = source_group.copy()
        node_group.name = config["unique_group_name"]

        # Clean up by removing the original imported group
        bpy.data.node_groups.remove(source_group)

        return node_group

    def _create_beatdriver_object(self, scene, config):
        """
        Create the object that will hold the BeatDriver geometry nodes modifier.

        Args:
            scene: The current Blender scene
            config: Project configuration dictionary

        Returns:
            Object: The created BeatDriver object
        """
        # Create empty mesh and object. The mesh is required for the geometry node modifier attachment.
        mesh = bpy.data.meshes.new(config["empty_name"])
        empty_obj = bpy.data.objects.new(config["empty_name"], mesh)

        # Add to scene
        scene.collection.objects.link(empty_obj)
        scene.beatdriver_object_name = empty_obj.name

        return empty_obj

    def _run_audio_analysis(self, config):
        """
        Execute the external audio analysis script to generate CSV data.

        Args:
            config: Project configuration dictionary

        Returns:
            bool: True if analysis completed successfully, False otherwise
        """
        try:
            # Get path to the audio analysis script
            addon_dir = os.path.dirname(__file__)
            script_path = os.path.join(addon_dir, "audio_analysis.py")

            # Run the external Python script for audio analysis
            subprocess.run(
                [
                    "python",
                    script_path,
                    config["dest_audio_path"],
                    config["csv_path"],
                    str(config["fps"]),
                ],
                check=True,
            )

            return True

        except subprocess.CalledProcessError as e:
            self.report({"ERROR"}, f"Audio analysis failed: {e}")
            return False
        except Exception as e:
            self.report({"ERROR"}, f"Unexpected error during audio analysis: {e}")
            return False

    def _setup_geometry_nodes_modifier(self, obj, node_group, config):
        """
        Set up the BeatDriver node on the object with CSV path.

        Args:
            obj: The object to add the modifier to
            node_group: The geometry node group to use
            config: Project configuration dictionary
        """
        # Create relative path to CSV file
        rel_csv_path = f"//{config['csv_name']}"

        # Add geometry nodes modifier
        gn_mod = obj.modifiers.new(name="BeatDriver", type="NODES")
        gn_mod.node_group = node_group

        # Set the relative CSV path in the node group input
        group_input_node = node_group.nodes.get("Group")
        if group_input_node:
            group_input_node.inputs[0].default_value = rel_csv_path
        else:
            self.report({"WARNING"}, "Group input node not found in node group")

    def _configure_timeline(self, scene, config):
        """
        Set the timeline end frame-count to the frame count gathered from the csv file.

        Args:
            scene: The current Blender scene
            config: Project configuration dictionary
        """
        try:
            # Count lines in CSV to determine timeline length
            with open(config["csv_path"], "r", encoding="utf-8") as f:
                num_lines = sum(1 for _ in f)

            # Set scene end frame to match data length
            scene.frame_end = num_lines
            scene.beatdriver_end_frame = scene.frame_end

        except Exception as e:
            self.report({"WARNING"}, f"Could not set frame_end from CSV: {e}")


# Registration
classes = [Select_Audio, Build_BeatDriver]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
