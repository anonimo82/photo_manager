import bpy
import os
import re

# --- Variabili Globali per lo Slideshow ---
slideshow_running = False
slideshow_index = 0
slideshow_items = []

def get_selected_materials(context):
    items = []
    if hasattr(context, "selected_assets") and context.selected_assets:
        items = context.selected_assets
    elif hasattr(context, "selected_asset_files") and context.selected_asset_files:
        items = context.selected_asset_files
    elif hasattr(context, "selected_ids") and context.selected_ids:
        items = context.selected_ids
        
    materials = []
    for item in items:
        mat = getattr(item, "local_id", item)
        if isinstance(mat, bpy.types.Material):
            materials.append(mat)
    return list(set(materials))

def slideshow_timer_callback():
    global slideshow_running, slideshow_index, slideshow_items
    if not slideshow_running or not slideshow_items:
        return None 
        
    slideshow_index = (slideshow_index + 1) % len(slideshow_items)
    mat = slideshow_items[slideshow_index]
    
    img = None
    if mat.use_nodes:
        for node in mat.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                img = node.image
                break
                
    if img:
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'IMAGE_EDITOR':
                    for space in area.spaces:
                        if space.type == 'IMAGE_EDITOR':
                            space.image = img
                            
    delay = 3.0
    if bpy.data.scenes:
        delay = bpy.data.scenes[0].photo_manager_tool.slideshow_delay
    return delay

# --- Operatori ---

class PHOTOMANAGER_OT_edit_image(bpy.types.Operator):
    """Esegue operazioni di trasformazione fisica sulle immagini selezionate e salva su disco"""
    bl_idname = "photo.edit_image"
    bl_label = "Modifica Immagine"
    
    action: bpy.props.StringProperty()
    
    def execute(self, context):
        tool = context.scene.photo_manager_tool
        assets = get_selected_materials(context)
        
        if not assets:
            self.report({'WARNING'}, "Nessun asset selezionato.")
            return {'CANCELLED'}
            
        import numpy as np
        count = 0
        
        for mat in assets:
            img = None
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image:
                        img = node.image
                        break
            if not img:
                continue
                
            # --- FIX DEFINITIVO: PERCORSI E BUFFER ---
            # 1. Ricostruiamo il percorso assoluto reale del file
            real_path = bpy.path.abspath(img.filepath)
            
            # 2. Se il file fisico non c'è più (es. spostato o cancellato), saltiamo e avvisiamo
            if not os.path.exists(real_path):
                self.report({'ERROR'}, f"File perso o spostato dal PC: {img.name}")
                continue
                
            # 3. Forziamo Blender ad aggiornare il percorso e a ricaricare dal disco
            if img.filepath != real_path:
                img.filepath = real_path
            
            img.reload()
            
            # 4. Tocchiamo un pixel a caso per forzare l'allocazione della RAM
            try:
                _ = img.pixels[0]
            except Exception:
                pass

            # --- INIZIO MODIFICA ---
            try:
                if self.action == 'RESIZE':
                    img.scale(tool.resize_width, tool.resize_height)
                    img.update()
                    
                else:
                    width, height = img.size
                    pixels = np.empty(width * height * 4, dtype=np.float32)
                    img.pixels.foreach_get(pixels)
                    pixels = pixels.reshape((height, width, 4))
                    
                    if self.action == 'FLIP_H':
                        pixels = np.fliplr(pixels)
                    elif self.action == 'FLIP_V':
                        pixels = np.flipud(pixels)
                    elif self.action == 'ROT_CW':
                        pixels = np.rot90(pixels, k=-1)
                        width, height = height, width
                    elif self.action == 'ROT_CCW':
                        pixels = np.rot90(pixels, k=1)
                        width, height = height, width
                        
                    if img.size[0] != width or img.size[1] != height:
                        img.scale(width, height)
                        
                    img.pixels.foreach_set(pixels.ravel())
                    img.update()
                
                # Rigenera anteprima e salva
                if getattr(mat, "asset_data", None):
                    mat.asset_generate_preview()
                    
                img.save()
                count += 1
                
            except Exception as e:
                self.report({'ERROR'}, f"Errore modificando {img.name}: {e}")
            
        if count > 0:
            self.report({'INFO'}, f"{count} immagini modificate e salvate su disco!")
        return {'FINISHED'}

class PHOTOMANAGER_OT_slideshow(bpy.types.Operator):
    bl_idname = "photo.slideshow_toggle"
    bl_label = "Slideshow"
    def execute(self, context):
        global slideshow_running, slideshow_index, slideshow_items
        if slideshow_running:
            slideshow_running = False
            self.report({'INFO'}, "Slideshow Fermato")
        else:
            slideshow_items = get_selected_materials(context)
            if not slideshow_items: return {'CANCELLED'}
            slideshow_index = 0
            slideshow_running = True
            bpy.app.timers.register(slideshow_timer_callback)
            self.report({'INFO'}, "Slideshow Avviato")
        return {'FINISHED'}

class PHOTOMANAGER_OT_view_image(bpy.types.Operator):
    bl_idname = "photo.view_image"
    bl_label = "Visualizza in Grande"
    def execute(self, context):
        assets = get_selected_materials(context)
        if not assets: return {'CANCELLED'}
        mat = assets[0] 
        img = None
        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    img = node.image
                    break
        if not img: return {'CANCELLED'}
        bpy.ops.wm.window_new()
        new_window = context.window_manager.windows[-1]
        for area in new_window.screen.areas:
            area.type = 'IMAGE_EDITOR'
            for space in area.spaces:
                if space.type == 'IMAGE_EDITOR':
                    space.image = img
                    space.show_region_ui = False 
                    space.show_region_tool_header = False
        return {'FINISHED'}

class PHOTOMANAGER_OT_import_assets(bpy.types.Operator):
    bl_idname = "photo.import_assets"
    bl_label = "Esegui Importazione"
    def execute(self, context):
        tool = context.scene.photo_manager_tool
        raw_dir = tool.target_folder
        if not raw_dir: return {'CANCELLED'}
        real_dir = os.path.normpath(bpy.path.abspath(raw_dir)).replace('\\', '/')
        if not os.path.exists(real_dir): return {'CANCELLED'}
        valid_ext = ('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff')
        files = [f for f in os.listdir(real_dir) if f.lower().endswith(valid_ext)]
        count = 0
        for f in files:
            file_path = os.path.join(real_dir, f)
            try:
                img = bpy.data.images.load(file_path, check_existing=True)
                mat_name = os.path.splitext(f)[0]
                mat = bpy.data.materials.get(mat_name)
                if not mat:
                    mat = bpy.data.materials.new(name=mat_name)
                    mat.use_nodes = True
                    mat.preview_render_type = 'FLAT' 
                    nodes = mat.node_tree.nodes
                    links = mat.node_tree.links
                    nodes.clear()
                    output = nodes.new(type='ShaderNodeOutputMaterial')
                    output.location = (300, 0)
                    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
                    bsdf.location = (0, 0)
                    tex = nodes.new(type='ShaderNodeTexImage')
                    tex.location = (-300, 0)
                    tex.image = img
                    links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
                    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
                if not getattr(mat, "asset_data", None): mat.asset_mark()
                mat.asset_generate_preview()
                count += 1
            except: pass
        self.report({'INFO'}, f"{count} foto importate!")
        return {'FINISHED'}

class PHOTOMANAGER_OT_rename_assets(bpy.types.Operator):
    bl_idname = "photo.rename_assets"
    bl_label = "Rinomina Selezionati"
    def execute(self, context):
        tool = context.scene.photo_manager_tool
        assets_to_rename = get_selected_materials(context)
        if not assets_to_rename: return {'CANCELLED'}
        assets_to_rename.sort(key=lambda mat: mat.name)
        count = 0; file_index = 0
        for mat in assets_to_rename:
            new_name = mat.name
            if tool.rename_find: new_name = new_name.replace(tool.rename_find, tool.rename_replace)
            if tool.rename_prefix: new_name = tool.rename_prefix + new_name
            if tool.rename_suffix: new_name = new_name + tool.rename_suffix
            if '#' in new_name:
                def replace_hash(match): return f"{file_index:0{len(match.group(1))}d}"
                new_name = re.sub(r'(#+)', replace_hash, new_name)
            if new_name != mat.name:
                mat.name = new_name
                if mat.use_nodes:
                    for node in mat.node_tree.nodes:
                        if node.type == 'TEX_IMAGE' and node.image:
                            node.image.name = new_name
                count += 1
            file_index += 1
        self.report({'INFO'}, f"{count} asset rinominati!")
        return {'FINISHED'}

class PHOTOMANAGER_OT_apply_tags(bpy.types.Operator):
    bl_idname = "photo.apply_tags"
    bl_label = "Aggiungi Tags"
    def execute(self, context):
        tool = context.scene.photo_manager_tool
        if not tool.batch_tags.strip(): return {'CANCELLED'}
        assets = get_selected_materials(context)
        if not assets: return {'CANCELLED'}
        new_tags = [t.strip() for t in tool.batch_tags.split(',') if t.strip()]
        for mat in assets:
            if getattr(mat, "asset_data", None):
                existing = [tag.name for tag in mat.asset_data.tags]
                for tag in new_tags:
                    if tag not in existing: mat.asset_data.tags.new(name=tag)
        return {'FINISHED'}

class PHOTOMANAGER_OT_clear_tags(bpy.types.Operator):
    bl_idname = "photo.clear_tags"
    bl_label = "Pulisci Tags"
    def execute(self, context):
        assets = get_selected_materials(context)
        for mat in assets:
            if getattr(mat, "asset_data", None):
                while mat.asset_data.tags:
                    mat.asset_data.tags.remove(mat.asset_data.tags[0])
        return {'FINISHED'}

class PHOTOMANAGER_OT_export_assets(bpy.types.Operator):
    bl_idname = "photo.export_assets"
    bl_label = "Esporta e Converti"
    def execute(self, context):
        tool = context.scene.photo_manager_tool
        raw_dir = tool.export_folder
        if not raw_dir: return {'CANCELLED'}
        real_dir = os.path.normpath(bpy.path.abspath(raw_dir)).replace('\\', '/')
        if not os.path.exists(real_dir): return {'CANCELLED'}
        assets = get_selected_materials(context)
        count = 0
        for mat in assets:
            img = None
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image: img = node.image
            if img:
                if tool.export_format != 'ORIGINAL':
                    img.file_format = tool.export_format
                    ext_map = {'PNG': '.png', 'JPEG': '.jpg', 'BMP': '.bmp', 'TARGA': '.tga', 'TIFF': '.tif'}
                    ext = ext_map.get(tool.export_format, '.png')
                else:
                    ext = os.path.splitext(img.filepath)[1] if getattr(img, 'filepath', None) else ".png"
                    if not ext: ext = ".png"
                new_filepath = os.path.join(real_dir, mat.name + ext)
                img.filepath_raw = new_filepath
                try:
                    img.save()
                    count += 1
                except: pass
        self.report({'INFO'}, f"{count} immagini esportate!")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(PHOTOMANAGER_OT_edit_image)
    bpy.utils.register_class(PHOTOMANAGER_OT_slideshow)
    bpy.utils.register_class(PHOTOMANAGER_OT_view_image)
    bpy.utils.register_class(PHOTOMANAGER_OT_import_assets)
    bpy.utils.register_class(PHOTOMANAGER_OT_rename_assets)
    bpy.utils.register_class(PHOTOMANAGER_OT_apply_tags)
    bpy.utils.register_class(PHOTOMANAGER_OT_clear_tags)
    bpy.utils.register_class(PHOTOMANAGER_OT_export_assets)

def unregister():
    bpy.utils.unregister_class(PHOTOMANAGER_OT_export_assets)
    bpy.utils.unregister_class(PHOTOMANAGER_OT_clear_tags)
    bpy.utils.unregister_class(PHOTOMANAGER_OT_apply_tags)
    bpy.utils.unregister_class(PHOTOMANAGER_OT_rename_assets)
    bpy.utils.unregister_class(PHOTOMANAGER_OT_import_assets)
    bpy.utils.unregister_class(PHOTOMANAGER_OT_view_image)
    bpy.utils.unregister_class(PHOTOMANAGER_OT_slideshow)
    bpy.utils.unregister_class(PHOTOMANAGER_OT_edit_image)