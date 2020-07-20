import json
import sys
sys.path.append("/media/becode/3D_House/")

import BlenderObjectBuilder as bob

import bpy
scene = bpy.context.scene

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

with open("/media/becode/3D_House/object_data.json") as read:
    data = json.load(read)
    mesh = bpy.data.meshes.new("terrain")
    mesh.from_pydata(*bob.Grid(data["terrain"]).data)
    obj = bpy.data.objects.new("terrain", mesh)
    scene.collection.objects.link(obj)
    for idx, entry in data["blocks"].items():
        mesh = bpy.data.meshes.new(str(idx))
        mesh.from_pydata(*bob.Prism(bob.Ngon(entry["vertices"]),entry["height"]).data)
        obj = bpy.data.objects.new(str(idx), mesh)
        scene.collection.objects.link(obj)
        
bpy.ops.wm.save_as_mainfile(filepath="./test.blend")