import bpy

class PHOTOMANAGER_PT_asset_panel(bpy.types.Panel):
    bl_label = "Gestore Foto"
    bl_idname = "PHOTOMANAGER_PT_asset_panel"
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS' 
    
    @classmethod
    def poll(cls, context):
        if hasattr(context.space_data, "browse_mode"):
            return context.space_data.browse_mode == 'ASSETS'
        return False
        
    def draw(self, context):
        layout = self.layout
        tool = context.scene.photo_manager_tool
        
        # --- RICERCA E VISUALIZZAZIONE ---
        layout.label(text="Cerca e Visualizza:", icon='VIEWZOOM')
        if hasattr(context.space_data, "params") and hasattr(context.space_data.params, "filter_search"):
            layout.prop(context.space_data.params, "filter_search", text="")
            
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("photo.view_image", icon='FULLSCREEN_ENTER', text="Vedi")
        
        from .operators import slideshow_running
        icon_slide = 'PAUSE' if slideshow_running else 'PLAY'
        text_slide = "Stop Slideshow" if slideshow_running else "Avvia Slideshow"
        
        row.operator("photo.slideshow_toggle", icon=icon_slide, text=text_slide)
        layout.prop(tool, "slideshow_delay", text="Intervallo (sec)")
        
        layout.separator()
        
        # --- 1. IMPORTAZIONE ---
        layout.label(text="1. Cartella Origine:", icon='FILE_FOLDER')
        layout.prop(tool, "target_folder", text="")
        layout.operator("photo.import_assets", icon='IMPORT')
        
        layout.separator()
        
        # --- 2. RINOMINA ---
        layout.label(text="2. Rinomina Asset:", icon='OUTLINER_OB_FONT')
        box = layout.box()
        box.prop(tool, "rename_prefix")
        box.prop(tool, "rename_suffix")
        box.separator()
        box.prop(tool, "rename_find")
        box.prop(tool, "rename_replace")
        layout.operator("photo.rename_assets", icon='FILE_TICK')
        
        layout.separator()
        
        # --- 3. ORGANIZZAZIONE ---
        layout.label(text="3. Organizzazione:", icon='BOOKMARKS')
        box = layout.box()
        box.prop(tool, "batch_tags", text="")
        row = box.row(align=True)
        row.operator("photo.apply_tags", icon='ADD')
        row.operator("photo.clear_tags", icon='TRASH')
        
        layout.separator()
        
        # --- 4. MODIFICA IMMAGINE ---
        layout.label(text="4. Modifica Immagine:", icon='IMAGE_DATA')
        box = layout.box()
        
        row = box.row(align=True)
        row.operator("photo.edit_image", icon='ARROW_LEFTRIGHT', text="Flip Orizz.").action = 'FLIP_H'
        row.operator("photo.edit_image", icon='SORT_ASC', text="Flip Vert.").action = 'FLIP_V'
        
        row = box.row(align=True)
        row.operator("photo.edit_image", icon='FILE_REFRESH', text="Ruota Orario").action = 'ROT_CW'
        row.operator("photo.edit_image", icon='FILE_REFRESH', text="Ruota Antior.").action = 'ROT_CCW'
        
        box.separator()
        box.label(text="Ridimensiona:")
        row = box.row(align=True)
        row.prop(tool, "resize_width", text="L")
        row.prop(tool, "resize_height", text="A")
        op = box.operator("photo.edit_image", icon='FULLSCREEN_ENTER', text="Applica")
        op.action = 'RESIZE'
        
        layout.separator()
        
        # --- 5. ESPORTAZIONE ---
        layout.label(text="5. Esporta e Converti:", icon='EXPORT')
        box = layout.box()
        box.prop(tool, "export_folder", text="Destinazione")
        box.prop(tool, "export_format", text="Formato")
        layout.operator("photo.export_assets", icon='RENDER_STILL')

def register():
    bpy.utils.register_class(PHOTOMANAGER_PT_asset_panel)

def unregister():
    bpy.utils.unregister_class(PHOTOMANAGER_PT_asset_panel)