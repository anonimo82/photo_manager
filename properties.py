import bpy
import os
from . import utils

def generate_image_previews(self, context):
    """Genera dinamicamente le miniature dalla cartella selezionata."""
    enum_items = []
    
    if context is None:
        return enum_items

    pcoll = utils.preview_collections.get("main")
    if not pcoll:
        return enum_items

    image_dir = context.scene.photo_manager_path

    if not image_dir or not os.path.exists(image_dir):
        return enum_items

    for p in pcoll:
        pcoll.remove(p)

    valid_extensions = ('.png', '.jpg', '.jpeg')
    
    for i, filename in enumerate(os.listdir(image_dir)):
        if filename.lower().endswith(valid_extensions):
            filepath = os.path.join(image_dir, filename)
            
            if filepath not in pcoll:
                thumb = pcoll.load(filepath, filepath, 'IMAGE')
            else:
                thumb = pcoll[filepath]
                
            enum_items.append((filepath, filename, "", thumb.icon_id, i))

    return enum_items

def register_properties():
    bpy.types.Scene.photo_manager_path = bpy.props.StringProperty(
        name="Cartella",
        description="Seleziona la cartella delle immagini",
        subtype='DIR_PATH'
    )
    
    bpy.types.Scene.photo_manager_thumbnails = bpy.props.EnumProperty(
        items=generate_image_previews,
        name="Seleziona Foto"
    )

def unregister_properties():
    del bpy.types.Scene.photo_manager_path
    del bpy.types.Scene.photo_manager_thumbnails