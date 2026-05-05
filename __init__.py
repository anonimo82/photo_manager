bl_info = {
    "name": "Photo Manager (Asset Browser)",
    "author": "Tu",
    "version": (1, 6),
    "blender": (3, 0, 0),
    "location": "Asset Browser > Sidebar (N)",
    "description": "Gestore completo foto: importazione, modifica fisica, tag, slideshow e conversione",
    "category": "System",
}

if "bpy" in locals():
    import importlib
    importlib.reload(properties)
    importlib.reload(operators)
    importlib.reload(ui)
else:
    from . import properties
    from . import operators
    from . import ui

import bpy

def register():
    properties.register()
    operators.register()
    ui.register()

def unregister():
    ui.unregister()
    operators.unregister()
    properties.unregister()

if __name__ == "__main__":
    register()