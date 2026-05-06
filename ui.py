import bpy

def draw_viewer_nav(self, context):
    from .operators import viewer_images, slideshow_running
    if len(viewer_images) > 0 and context.space_data and context.space_data.type == 'IMAGE_EDITOR':
        if context.space_data.image in viewer_images:
            idx = viewer_images.index(context.space_data.image)
            layout = self.layout
            tool = context.scene.photo_manager_tool
            layout.separator()
            row = layout.row(align=True)
            op_prev = row.operator("photo.view_nav", icon='TRIA_LEFT', text="")
            op_prev.direction = -1
            row.label(text=f" {idx + 1} / {len(viewer_images)} ")
            op_next = row.operator("photo.view_nav", icon='TRIA_RIGHT', text="")
            op_next.direction = 1
            layout.separator()
            icon = 'PAUSE' if slideshow_running else 'PLAY'
            layout.operator("photo.slideshow_toggle", icon=icon, text="")
            layout.prop(tool, "slideshow_delay", text="Sec")

class PHOTOMANAGER_PT_asset_panel(bpy.types.Panel):
    bl_label = "Photo Manager"
    bl_idname = "PHOTOMANAGER_PT_asset_panel"
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS' 
    
    @classmethod
    def poll(cls, context):
        return getattr(context.space_data, "browse_mode", None) == 'ASSETS'
        
    def draw(self, context):
        layout = self.layout
        tool = context.scene.photo_manager_tool
        
        # SEARCH & VIEW
        layout.label(text="Search and View:", icon='VIEWZOOM')
        if hasattr(context.space_data, "params"):
            layout.prop(context.space_data.params, "filter_search", text="")
            
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("photo.view_image", icon='FULLSCREEN_ENTER')
        
        layout.separator()
        
        # 1. IMPORT
        layout.label(text="1. Source Folder:", icon='FILE_FOLDER')
        layout.prop(tool, "target_folder", text="")
        layout.operator("photo.import_assets", icon='IMPORT')
        
        # 2. RENAME
        layout.label(text="2. Rename Assets:", icon='OUTLINER_OB_FONT')
        box = layout.box()
        box.label(text="Rename Template:", icon='FILE_TEXT')
        box.prop(tool, "rename_template", text="")
        box.label(text="Use: <NAME>  <DATA>  <TIME>  #", icon='INFO')
        box.separator()
        box.label(text="Clean original <NAME>:", icon='BRUSH_DATA')
        col = box.column(align=True)
        col.prop(tool, "rename_find")
        col.prop(tool, "rename_replace")
        col.prop(tool, "rename_remove")
        box.prop(tool, "rename_case", text="Format")
        layout.operator("photo.rename_assets", icon='FILE_TICK')
        
        # 3. ORGANIZATION
        layout.label(text="3. Organization:", icon='BOOKMARKS')
        box = layout.box()
        box.prop(tool, "batch_tags", text="")
        row = box.row(align=True)
        row.operator("photo.apply_tags", icon='ADD')
        row.operator("photo.clear_tags", icon='TRASH')
        
        # 4. EDIT
        layout.label(text="4. Edit Image:", icon='IMAGE_DATA')
        box = layout.box()
        row = box.row(align=True)
        row.operator("photo.edit_image", text="Flip H").action = 'FLIP_H'
        row.operator("photo.edit_image", text="Flip V").action = 'FLIP_V'
        row = box.row(align=True)
        row.operator("photo.edit_image", text="Rotate CW").action = 'ROT_CW'
        row.operator("photo.edit_image", text="Rotate CCW").action = 'ROT_CCW'
        box.separator()
        
        items = getattr(context, "selected_assets", getattr(context, "selected_asset_files", []))
        cw, ch = 0, 0
        if items:
            m = getattr(items[0], "local_id", items[0])
            if hasattr(m, "use_nodes") and m.use_nodes:
                img = next((n.image for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image), None)
                if img: cw, ch = img.size[0], img.size[1]
        
        row = box.row(align=True)
        row.label(text=f"Original: {cw}x{ch}" if cw > 0 else "Resize:")
        row.operator("photo.get_dimensions", icon='FILE_REFRESH', text="")
        
        row = box.row(align=True)
        row.prop(tool, "resize_width", text="W"); row.prop(tool, "resize_height", text="H")
        op = box.operator("photo.edit_image", text="Apply Resize")
        op.action = 'RESIZE'
        
        # 5. EXPORT
        layout.label(text="5. Export and Convert:", icon='EXPORT')
        box = layout.box()
        box.prop(tool, "export_folder", text="Path")
        box.prop(tool, "export_format", text="Fmt")
        layout.operator("photo.export_assets", icon='RENDER_STILL')

def register():
    bpy.utils.register_class(PHOTOMANAGER_PT_asset_panel)
    bpy.types.IMAGE_HT_header.append(draw_viewer_nav)

def unregister():
    bpy.types.IMAGE_HT_header.remove(draw_viewer_nav)
    bpy.utils.unregister_class(PHOTOMANAGER_PT_asset_panel)