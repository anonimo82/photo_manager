import bpy

class PhotoManagerSettings(bpy.types.PropertyGroup):
    target_folder: bpy.props.StringProperty(
        name="Origine",
        description="Seleziona la cartella da cui importare le foto",
        subtype='DIR_PATH',
        default=""
    )
    export_folder: bpy.props.StringProperty(
        name="Export",
        description="Seleziona dove salvare i file elaborati",
        subtype='DIR_PATH',
        default=""
    )
    rename_prefix: bpy.props.StringProperty(name="Prefisso")
    rename_suffix: bpy.props.StringProperty(name="Suffisso")
    rename_find: bpy.props.StringProperty(name="Trova")
    rename_replace: bpy.props.StringProperty(name="Sostituisci")
    
    batch_tags: bpy.props.StringProperty(
        name="Tags",
        description="Inserisci i tag separati da virgola",
        default=""
    )
    export_format: bpy.props.EnumProperty(
        name="Formato",
        description="Scegli il formato in cui convertire le immagini",
        items=[
            ('ORIGINAL', "Originale", "Mantiene il formato di partenza"),
            ('PNG', "PNG", "Senza perdita di qualità, supporta trasparenza"),
            ('JPEG', "JPEG", "Formato compresso, ideale per il web"),
            ('BMP', "BMP", "Bitmap standard"),
            ('TARGA', "TGA", "Formato Targa, usato spesso nei videogiochi"),
            ('TIFF', "TIFF", "Alta qualità per la stampa")
        ],
        default='ORIGINAL'
    )
    slideshow_delay: bpy.props.FloatProperty(
        name="Secondi",
        description="Tempo di attesa tra una foto e l'altra",
        default=3.0,
        min=0.1,
        max=60.0
    )
    
    # --- PROPRIETÀ PER IL RIDIMENSIONAMENTO ---
    resize_width: bpy.props.IntProperty(
        name="Larghezza",
        description="Nuova larghezza in pixel",
        default=1024,
        min=1
    )
    resize_height: bpy.props.IntProperty(
        name="Altezza",
        description="Nuova altezza in pixel",
        default=1024,
        min=1
    )

def register():
    bpy.utils.register_class(PhotoManagerSettings)
    bpy.types.Scene.photo_manager_tool = bpy.props.PointerProperty(type=PhotoManagerSettings)

def unregister():
    bpy.utils.unregister_class(PhotoManagerSettings)
    del bpy.types.Scene.photo_manager_tool