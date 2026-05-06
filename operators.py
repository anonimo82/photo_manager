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
        area = context.window_manager.windows[-1].screen.areas[0]
        area.type = 'IMAGE_EDITOR'
        area.spaces.active.image = viewer_images[0]
        area.spaces.active.show_region_ui = False 
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
        assets = get_selected_materials(context)
        for mat in assets:
            img = next((n.image for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image), None) if mat.use_nodes else None
            if not img: continue
            force_image_load(img)
            try:
                if self.action == 'RESIZE': img.scale(tool.resize_width, tool.resize_height)
                else:
                    w, h = img.size
                    pixels = np.empty(w * h * 4, dtype=np.float32)
                    img.pixels.foreach_get(pixels)
                    pixels = pixels.reshape((h, w, 4))
                    if self.action == 'FLIP_H': pixels = np.fliplr(pixels)
                    elif self.action == 'FLIP_V': pixels = np.flipud(pixels)
                    elif self.action == 'ROT_CW': pixels = np.rot90(pixels, k=-1); w, h = h, w
                    elif self.action == 'ROT_CCW': pixels = np.rot90(pixels, k=1); w, h = h, w
                    if img.size[0] != w or img.size[1] != h: img.scale(w, h)
                    img.pixels.foreach_set(pixels.ravel())
                img.update()
                img.save()
            except Exception as e: print(e)
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
            if tool.rename_find: bn = bn.replace(tool.rename_find, tool.rename_replace)
            if tool.rename_case == 'LOWER': bn = bn.lower()
            elif tool.rename_case == 'UPPER': bn = bn.upper()
            elif tool.rename_case == 'TITLE': bn = bn.replace('_', ' ').replace('-', ' ').title()
            elif tool.rename_case == 'SNAKE': bn = re.sub(r'[\s\-]+', '_', bn).lower()
            elif tool.rename_case == 'CAMEL':
                parts = re.split(r'[\s_\-]+', bn)
                if parts: bn = parts[0].lower() + ''.join(w.capitalize() for w in parts[1:])
            elif tool.rename_case == 'PASCAL':
                parts = re.split(r'[\s_\-]+', bn)
                bn = ''.join(w.capitalize() for w in parts)
            
            fn = tool.rename_template.replace("<NAME>", bn).replace("<DATA>", dt).replace("<ORA>", tm)
            if '#' in fn: fn = re.sub(r'(#+)', lambda mh: f"{i:0{len(mh.group(1))}d}", fn)
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
        for m in get_selected_materials(context):
            img = next((n.image for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image), None) if m.use_nodes else None
            if img:
                if tool.export_format != 'ORIGINAL': img.file_format = tool.export_format
                ext = ".jpg" if img.file_format == 'JPEG' else ".png"
                img.filepath_raw = os.path.join(dest, m.name + ext)
                img.save()
        return {'FINISHED'}

def register():
    bpy.utils.register_class(PHOTOMANAGER_OT_view_nav)
    bpy.utils.register_class(PHOTOMANAGER_OT_get_dimensions)
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
    bpy.utils.unregister_class(PHOTOMANAGER_OT_get_dimensions)
    bpy.utils.unregister_class(PHOTOMANAGER_OT_view_nav)