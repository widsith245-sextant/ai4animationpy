"""Reusable application programs layered on top of the low-level ECS runtime."""

from ai4animation.AI4Animation import AI4Animation
from ai4animation.Animation.Dataset import Dataset
from ai4animation.Components.Actor import Actor
from ai4animation.Components.MotionEditor import MotionEditor
from ai4animation.Math import Rotation, Vector3
from ai4animation import Time

from .Config import ActorViewerConfig, MotionEditorConfig


class EmptyProgram:
    def __init__(self, on_start=None, on_update=None):
        self._on_start = on_start
        self._on_update = on_update

    def Start(self):
        if self._on_start is not None:
            self._on_start()

    def Update(self):
        if self._on_update is not None:
            self._on_update()


class ActorViewerProgram:
    def __init__(self, config: ActorViewerConfig):
        self.Config = config
        self.Actor = None

    def Start(self):
        entity = AI4Animation.Scene.AddEntity(self.Config.entity_name)
        self.Actor = entity.AddComponent(
            Actor,
            self.Config.model_path,
            list(self.Config.skeleton.bone_names),
        )
        entity.SetPosition(Vector3.Create(*self.Config.position))

        if AI4Animation.IsStandalone():
            AI4Animation.Standalone.Camera.SetTarget(entity)

    def Update(self):
        if self.Actor is None or self.Config.auto_rotate_degrees_per_second == 0.0:
            return

        self.Actor.Entity.SetRotation(
            Rotation.Euler(
                0.0,
                self.Config.auto_rotate_degrees_per_second * Time.TotalTime,
                0.0,
            )
        )
        self.Actor.SyncFromScene()


class MotionEditorProgram:
    def __init__(self, config: MotionEditorConfig):
        self.Config = config
        self.Dataset = None
        self.Editor = None

    def Start(self):
        self.Dataset = Dataset(
            self.Config.dataset_directory,
            self.Config.create_modules(),
            max_files=self.Config.max_files,
        )

        editor = AI4Animation.Scene.AddEntity(self.Config.entity_name)
        self.Editor = editor.AddComponent(
            MotionEditor,
            self.Dataset,
            self.Config.model_path,
            list(self.Config.skeleton.bone_names),
        )

        if AI4Animation.IsStandalone():
            AI4Animation.Standalone.Camera.SetTarget(editor)

    def Update(self):
        return
