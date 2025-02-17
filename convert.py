import bpy
import sys
import os

# Obter argumentos após "--"
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
else:
    argv = []

if len(argv) < 3:
    print("Uso: blender --background --python convert.py -- <input_path> <output_path> <target_format>")
    sys.exit(1)

input_path = argv[0]
output_path = argv[1]
target_format = argv[2].lower()

# Limpa a cena
bpy.ops.wm.read_factory_settings(use_empty=True)

# Importa o modelo com base na extensão do arquivo
ext = os.path.splitext(input_path)[1].lower()

if ext == ".obj":
    bpy.ops.import_scene.obj(filepath=input_path)
elif ext == ".fbx":
    bpy.ops.import_scene.fbx(filepath=input_path)
elif ext in [".gltf", ".glb"]:
    bpy.ops.import_scene.gltf(filepath=input_path)
elif ext == ".blend":
    # Para arquivos .blend, carrega o arquivo principal
    bpy.ops.wm.open_mainfile(filepath=input_path)
else:
    print("Formato de entrada não suportado:", ext)
    sys.exit(1)

# Exporta para o formato de destino escolhido
if target_format == "fbx":
    bpy.ops.export_scene.fbx(filepath=output_path)
elif target_format == "obj":
    bpy.ops.export_scene.obj(filepath=output_path)
elif target_format == "gltf":
    bpy.ops.export_scene.gltf(filepath=output_path)
elif target_format == "glb":
    bpy.ops.export_scene.gltf(filepath=output_path, export_format='GLB')
elif target_format == "blend":
    bpy.ops.wm.save_as_mainfile(filepath=output_path)
elif target_format == "usdz":
    # USDZ não é suportado nativamente pelo Blender sem add-ons adicionais.
    print("Exportação para USDZ não é suportada por este script.")
    sys.exit(1)
else:
    print("Formato de destino não suportado:", target_format)
    sys.exit(1)

sys.exit(0)
