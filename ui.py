import bpy

class PHOTOMANAGER_PT_panel(bpy.types.Panel):
    """Crea un Pannello nella Sidebar della Vista 3D"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Foto'
    bl_label = "Gestione Foto"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "photo_manager_path")

        if scene.photo_manager_path:
            layout.template_icon_view(scene, "photo_manager_thumbnails", show_labels=True)
            
            if scene.photo_manager_thumbnails:
                layout.operator("photo.load_action", text="Carica Immagine")

def register_ui():
    bpy.utils.register_class(PHOTOMANAGER_PT_panel)

def unregister_ui():
    bpy.utils.unregister_class(PHOTOMANAGER_PT_panel)