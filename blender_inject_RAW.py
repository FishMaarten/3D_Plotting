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
    for ftype, tif in data.items():
        mesh = bpy.data.meshes.new(ftype)
        mesh.from_pydata(*bob.Grid(tif).data)
        obj = bpy.data.objects.new(ftype, mesh)
        scene.collection.objects.link(obj)
    
bpy.ops.wm.save_as_mainfile(filepath="./test.blend")