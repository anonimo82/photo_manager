import bpy
import os

class PHOTOMANAGER_OT_load(bpy.types.Operator):
    """Carica la foto selezionata nell'Image Editor"""
    bl_idname = "photo.load_action"
    bl_label = "Carica Foto"

    def execute(self, context):
        filepath = context.scene.photo_manager_thumbnails
        if filepath and os.path.exists(filepath):
            bpy.ops.image.open(filepath=filepath)
            self.report({'INFO'}, f"Immagine caricata: {os.path.basename(filepath)}")
        return {'FINISHED'}

def register_operators():
    bpy.utils.register_class(PHOTOMANAGER_OT_load)

def unregister_operators():
    bpy.utils.unregister_class(PHOTOMANAGER_OT_load)