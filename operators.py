import bpy
import os
import re
import numpy as np
from datetime import datetime

viewer_images = []
viewer_index = 0
slideshow_running = False

def get_selected_materials(context):
    items = getattr(context, "selected_assets", getattr(context, "selected_asset_files", getattr(context, "selected_ids", [])))
    return list(set(getattr(item, "local_id", item) for item in items if isinstance(getattr(item, "local_id", item), bpy.types.Material)))

def force_image_load(img):
    if not img: return
    try:
        img.display_aspect = (1.0, 1.0) # Previene deformazioni del file
        if img.has_data and len(img.pixels) > 0: return
    except Exception: pass
    try:
        real_path = bpy.path.abspath(img.filepath)
        if os.path.exists(real_path):
            img.source = 'GENERATED'
            img.source = 'FILE'
            img.filepath = real_path
            img.reload()
            _ = img.pixels[0]
            img.gl_load()
            img.update()
    except Exception: pass

# --- SISTEMA DI ZOOM "SHRINK TO FIT" CORAZZATO ---
def apply_zoom_to_area(window, area, img):
    """Calcola e applica lo zoom preservando rigorosamente l'aspect ratio"""
    try:
        region = next((r for r in area.regions if r.type == 'WINDOW'), None)
        if not region or region.width < 50: return False
        
        img_w, img_h = img.size
        # Se l'immagine non è ancora in RAM, fermiamo il calcolo
        if img_w < 10 or img_h < 10: return False 
        
        # Calcolo Shrink to Fit (5% di margine)
        zoom_x = (region.width * 0.95) / float(img_w)
        zoom_y = (region.height * 0.95) / float(img_h)
        
        # Prende il valore più piccolo ma NON supera mai 1.0 (Shrink to Fit)
        zoom_factor = float(min(zoom_x, zoom_y, 1.0))
        
        space = area.spaces.active
        
        # Metodo 1: Assegnazione diretta
        try:
            space.zoom = (zoom_factor, zoom_factor)
            if hasattr(space, "offset"): space.offset = (0.0, 0.0) # Centra
        except: pass
        
        # Metodo 2: Fallback tramite operatore (se la UI non si aggiorna)
        try:
            with bpy.context.temp_override(window=window, area=area, region=region):
                bpy.ops.image.view_zoom_ratio(ratio=zoom_factor)
        except: pass
        
        return True
    except Exception:
        return False

def make_delayed_zoom(img_name, retries=15):
    """Timer continuo: aspetta che l'immagine grande sia pronta prima di zoomare"""
    state = {'retries': retries}
    def zoom_timer():
        img = bpy.data.images.get(img_name)
        if not img: return None
        
        for w in bpy.context.window_manager.windows:
            for a in w.screen.areas:
                if a.type == 'IMAGE_EDITOR' and a.spaces.active and a.spaces.active.image == img:
                    apply_zoom_to_area(w, a, img)
                    a.tag_redraw()
                    
        # Il timer continua a girare fino a esaurimento per essere sicuro 
        # che Blender abbia caricato e renderizzato correttamente le dimensioni finali
        state['retries'] -= 1
        return 0.05 if state['retries'] > 0 else None
    return zoom_timer

def slideshow_timer_callback():
    global slideshow_running, viewer_images, viewer_index
    if not slideshow_running or not viewer_images: return None 
    viewer_index = (viewer_index + 1) % len(viewer_images)
    img = viewer_images[viewer_index]
    force_image_load(img)
    
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.type == 'IMAGE_EDITOR': 
                a.spaces.active.image = img
                a.tag_redraw()
    
    # Timer rapido per lo zoom post-caricamento
    bpy.app.timers.register(make_delayed_zoom(img.name, retries=5), first_interval=0.01)
                
    return bpy.data.scenes[0].photo_manager_tool.slideshow_delay if bpy.data.scenes else 3.0


class PHOTOMANAGER_OT_view_nav(bpy.types.Operator):
    bl_idname = "photo.view_nav"
    bl_label = "Navigate"
    direction: bpy.props.IntProperty()
    def execute(self, context):
        global viewer_images, viewer_index
        if not viewer_images: return {'CANCELLED'}
        viewer_index = (viewer_index + self.direction) % len(viewer_images)
        img = viewer_images[viewer_index]
        force_image_load(img)
        
        if context.area and context.area.type == 'IMAGE_EDITOR':
            context.space_data.image = img
            context.area.tag_redraw()
            
        # Timer per lo zoom sicuro
        bpy.app.timers.register(make_delayed_zoom(img.name, retries=5), first_interval=0.01)
            
        return {'FINISHED'}

class PHOTOMANAGER_OT_view_image(bpy.types.Operator):
    bl_idname = "photo.view_image"
    bl_label = "Open Selected in Viewer"
    def execute(self, context):
        global viewer_images, viewer_index
        assets = get_selected_materials(context)
        if not assets: return {'CANCELLED'}
        viewer_images = []
        for mat in assets:
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image and node.image not in viewer_images:
                        viewer_images.append(node.image)
        if not viewer_images: return {'CANCELLED'}
        viewer_index = 0
        force_image_load(viewer_images[0])
        
        bpy.ops.wm.window_new()
        win = context.window_manager.windows[-1]
        area = win.screen.areas[0]
        area.type = 'IMAGE_EDITOR'
        space = area.spaces.active
        space.image = viewer_images[0]
        space.show_region_ui = False 
        
        # Lanciamo il timer lungo (15 cicli) per dare tempo alla finestra e all'immagine di esistere
        bpy.app.timers.register(make_delayed_zoom(viewer_images[0].name, retries=15), first_interval=0.05)
            
        return {'FINISHED'}

class PHOTOMANAGER_OT_slideshow(bpy.types.Operator):
    bl_idname = "photo.slideshow_toggle"
    bl_label = "Slideshow"
    def execute(self, context):
        global slideshow_running, viewer_images
        if slideshow_running: slideshow_running = False
        else:
            if not viewer_images: return {'CANCELLED'}
            slideshow_running = True
            bpy.app.timers.register(slideshow_timer_callback)
        return {'FINISHED'}

class PHOTOMANAGER_OT_edit_image(bpy.types.Operator):
    bl_idname = "photo.edit_image"
    bl_label = "Edit Image"
    action: bpy.props.StringProperty()
    
    def execute(self, context):
        tool = context.scene.photo_manager_tool
        selected_mats = get_selected_materials(context)
        if not selected_mats: return {'CANCELLED'}

        for mat in selected_mats:
            img = next((n.image for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image), None) if mat.use_nodes else None
            if not img: continue
            
            force_image_load(img)
            try:
                w, h = img.size
                pixels = np.empty(w * h * 4, dtype=np.float32)
                img.pixels.foreach_get(pixels)
                pixels = pixels.reshape((h, w, 4))
                
                if self.action == 'RESIZE': 
                    img.scale(tool.resize_width, tool.resize_height)
                else:
                    if self.action == 'FLIP_H': 
                        pixels = np.fliplr(pixels)
                    elif self.action == 'FLIP_V': 
                        pixels = np.flipud(pixels)
                    elif self.action == 'ROT_CW': 
                        pixels = np.flipud(np.transpose(pixels, (1, 0, 2)))
                        w, h = h, w
                    elif self.action == 'ROT_CCW': 
                        pixels = np.fliplr(np.transpose(pixels, (1, 0, 2)))
                        w, h = h, w
                    
                    if img.size[0] != w or img.size[1] != h: 
                        img.scale(w, h)
                    
                    pixels = np.ascontiguousarray(pixels).flatten()
                    img.pixels.foreach_set(pixels)
                
                img.display_aspect = (1.0, 1.0)
                img.update()
                img.save() 
                
            except Exception as e: 
                print(f"Errore Edit su {img.name}: {e}")

        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type in {'IMAGE_EDITOR', 'VIEW_3D', 'FILE_BROWSER'}:
                    area.tag_redraw()

        return {'FINISHED'}

class PHOTOMANAGER_OT_update_previews(bpy.types.Operator):
    bl_idname = "photo.update_previews"
    bl_label = "Update Thumbnails"
    bl_description = "Rigenera le miniature nell'Asset Browser (Attenzione: deseleziona gli asset)"
    
    def execute(self, context):
        selected_mats = get_selected_materials(context)
        if not selected_mats: return {'CANCELLED'}
        
        for mat in selected_mats:
            if hasattr(mat, "asset_generate_preview"):
                mat.asset_generate_preview()
                
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'FILE_BROWSER':
                    area.tag_redraw()
                    
        return {'FINISHED'}

class PHOTOMANAGER_OT_get_dimensions(bpy.types.Operator):
    bl_idname = "photo.get_dimensions"
    bl_label = "Sync Dimensions"
    def execute(self, context):
        assets = get_selected_materials(context)
        if assets:
            tool = context.scene.photo_manager_tool
            mat = assets[0]
            img = next((n.image for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image), None) if mat.use_nodes else None
            if img: tool.resize_width, tool.resize_height = img.size[0], img.size[1]
        return {'FINISHED'}

class PHOTOMANAGER_OT_import_assets(bpy.types.Operator):
    bl_idname = "photo.import_assets"
    bl_label = "Import"
    def execute(self, context):
        tool = context.scene.photo_manager_tool
        p = bpy.path.abspath(tool.target_folder)
        if not os.path.exists(p): return {'CANCELLED'}
        files = [f for f in os.listdir(p) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.bmp'))]
        for f in files:
            file_path = os.path.abspath(os.path.join(p, f))
            img = bpy.data.images.load(file_path, check_existing=True)
            img.filepath = file_path 
            img.display_aspect = (1.0, 1.0)
            name = os.path.splitext(f)[0]
            mat = bpy.data.materials.get(name) or bpy.data.materials.new(name=name)
            mat.use_nodes = True
            mat.preview_render_type = 'FLAT'
            nodes = mat.node_tree.nodes
            nodes.clear()
            tex = nodes.new('ShaderNodeTexImage'); tex.image = img
            out = nodes.new('ShaderNodeOutputMaterial')
            mat.node_tree.links.new(tex.outputs[0], out.inputs[0])
            if not getattr(mat, "asset_data", None): mat.asset_mark()
            mat.asset_generate_preview()
        return {'FINISHED'}

class PHOTOMANAGER_OT_rename_assets(bpy.types.Operator):
    bl_idname = "photo.rename_assets"
    bl_label = "Rename"
    def execute(self, context):
        tool = context.scene.photo_manager_tool
        assets = get_selected_materials(context)
        assets.sort(key=lambda m: m.name)
        dt = datetime.now().strftime("%Y%m%d")
        tm = datetime.now().strftime("%H%M")
        
        for i, m in enumerate(assets):
            bn = m.name
            if tool.rename_remove:
                for r in tool.rename_remove.split(','): bn = bn.replace(r.strip(), "")
            if tool.rename_find: 
                bn = bn.replace(tool.rename_find, tool.rename_replace)
                
            case_type = tool.rename_case.upper()
            
            if case_type.startswith('LOWER'): 
                bn = bn.lower()
            elif case_type.startswith('UPPER'): 
                bn = bn.upper()
            elif case_type.startswith('TITLE'): 
                bn = bn.replace('_', ' ').replace('-', ' ').title()
            elif case_type.startswith('SNAKE'): 
                bn = re.sub(r'[^a-zA-Z0-9]+', '_', bn).lower()
            elif case_type.startswith('CAMEL'):
                parts = [p for p in re.split(r'[^a-zA-Z0-9]+', bn) if p]
                if parts: 
                    bn = parts[0].lower() + ''.join(p.capitalize() for p in parts[1:])
            elif case_type.startswith('PASCAL'):
                parts = [p for p in re.split(r'[^a-zA-Z0-9]+', bn) if p]
                if parts: 
                    bn = ''.join(p.capitalize() for p in parts)
            
            fn = tool.rename_template.replace("<NAME>", bn).replace("<DATA>", dt).replace("<ORA>", tm)
            if '#' in fn: 
                fn = re.sub(r'(#+)', lambda mh: f"{i:0{len(mh.group(1))}d}", fn)
                
            m.name = fn
            if m.use_nodes:
                for node in m.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image: node.image.name = fn
                    
        return {'FINISHED'}

class PHOTOMANAGER_OT_apply_tags(bpy.types.Operator):
    bl_idname = "photo.apply_tags"
    bl_label = "Apply Tags"
    def execute(self, context):
        tool = context.scene.photo_manager_tool
        tags = [t.strip() for t in tool.batch_tags.split(',') if t.strip()]
        for m in get_selected_materials(context):
            if getattr(m, "asset_data", None):
                for t in tags:
                    if t not in [et.name for et in m.asset_data.tags]: m.asset_data.tags.new(name=t)
        return {'FINISHED'}

class PHOTOMANAGER_OT_clear_tags(bpy.types.Operator):
    bl_idname = "photo.clear_tags"
    bl_label = "Clear Tags"
    def execute(self, context):
        for m in get_selected_materials(context):
            if getattr(m, "asset_data", None):
                while m.asset_data.tags: m.asset_data.tags.remove(m.asset_data.tags[0])
        return {'FINISHED'}

class PHOTOMANAGER_OT_export_assets(bpy.types.Operator):
    bl_idname = "photo.export_assets"
    bl_label = "Export Assets"
    def execute(self, context):
        tool = context.scene.photo_manager_tool
        dest = bpy.path.abspath(tool.export_folder)
        if not os.path.exists(dest): return {'CANCELLED'}
        
        scene = context.scene
        old_format = scene.render.image_settings.file_format
        old_color_mode = scene.render.image_settings.color_mode
        
        if tool.export_format != 'ORIGINAL':
            scene.render.image_settings.file_format = tool.export_format
            if tool.export_format == 'JPEG':
                scene.render.image_settings.color_mode = 'RGB' 
        
        for m in get_selected_materials(context):
            img = next((n.image for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image), None) if m.use_nodes else None
            if img:
                ext = ".jpg" if tool.export_format == 'JPEG' else (".png" if tool.export_format == 'PNG' else ".tif")
                if tool.export_format == 'ORIGINAL':
                    ext = os.path.splitext(img.filepath)[1] or ".png"
                
                target_path = os.path.join(dest, m.name + ext)
                
                if tool.export_format != 'ORIGINAL':
                    img.save_render(filepath=target_path, scene=scene)
                else:
                    img.save_render(filepath=target_path)
                    
        scene.render.image_settings.file_format = old_format
        scene.render.image_settings.color_mode = old_color_mode
        
        return {'FINISHED'}

def register():
    bpy.utils.register_class(PHOTOMANAGER_OT_view_nav)
    bpy.utils.register_class(PHOTOMANAGER_OT_get_dimensions)
    bpy.utils.register_class(PHOTOMANAGER_OT_edit_image)
    bpy.utils.register_class(PHOTOMANAGER_OT_update_previews)
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
    bpy.utils.unregister_class(PHOTOMANAGER_OT_update_previews)
    bpy.utils.unregister_class(PHOTOMANAGER_OT_edit_image)
    bpy.utils.unregister_class(PHOTOMANAGER_OT_get_dimensions)
    bpy.utils.unregister_class(PHOTOMANAGER_OT_view_nav)