bl_info = {
    "name": "Photo Manager",
    "author": "Tu",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Foto",
    "description": "Gestore di foto diviso in moduli",
    "category": "3D View",
}

# Sistema di auto-reload dei moduli per lo sviluppo
if "bpy" in locals():
    import importlib
    importlib.reload(utils)
    importlib.reload(properties)
    importlib.reload(operators)
    importlib.reload(ui)
else:
    from . import utils
    from . import properties
    from . import operators
    from . import ui

import bpy
import bpy.utils.previews

def register():
    # Inizializza la collezione di anteprime nel modulo utils
    pcoll = bpy.utils.previews.new()
    utils.preview_collections["main"] = pcoll

    # Richiama le registrazioni dai vari moduli
    properties.register_properties()
    operators.register_operators()
    ui.register_ui()

def unregister():
    # Pulisci le anteprime dalla memoria
    for pcoll in utils.preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    utils.preview_collections.clear()

    # Deregistra in ordine inverso
    ui.unregister_ui()
    operators.unregister_operators()
    properties.unregister_properties()

if __name__ == "__main__":
    register()