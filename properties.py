import bpy

class PhotoManagerSettings(bpy.types.PropertyGroup):
    target_folder: bpy.props.StringProperty(name="Source", subtype='DIR_PATH', default="")
    export_folder: bpy.props.StringProperty(name="Export", subtype='DIR_PATH', default="")
    
    # --- TEMPLATE SYSTEM ---
    rename_template: bpy.props.StringProperty(
        name="Template",
        description="Use <NAME>, <DATE>, <TIME> and # for numbering",
        default="<NAME>"
    )
    
    # Clean up
    rename_find: bpy.props.StringProperty(name="Find")
    rename_replace: bpy.props.StringProperty(name="Replace")
    rename_remove: bpy.props.StringProperty(name="Remove")
    rename_case: bpy.props.EnumProperty(
        name="Text Case",
        items=[
            ('NONE', "Original", ""), ('LOWER', "lowercase", ""), 
            ('UPPER', "UPPERCASE", ""), ('TITLE', "Title Case", ""), 
            ('SNAKE', "snake_case", ""), ('CAMEL', "camelCase", ""), 
            ('PASCAL', "PascalCase", "")
        ],
        default='NONE'
    )
    
    batch_tags: bpy.props.StringProperty(name="Tags")
    export_format: bpy.props.EnumProperty(
        name="Format",
        items=[('ORIGINAL', "Original", ""), ('PNG', "PNG", ""), ('JPEG', "JPEG", "")]
    )
    slideshow_delay: bpy.props.FloatProperty(name="Seconds", default=3.0, min=0.1)
    resize_width: bpy.props.IntProperty(name="Width", default=1024, min=1)
    resize_height: bpy.props.IntProperty(name="Height", default=1024, min=1)

def register():
    bpy.utils.register_class(PhotoManagerSettings)
    bpy.types.Scene.photo_manager_tool = bpy.props.PointerProperty(type=PhotoManagerSettings)

def unregister():
    bpy.utils.unregister_class(PhotoManagerSettings)
    del bpy.types.Scene.photo_manager_tool