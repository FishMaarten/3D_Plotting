import json
import sys
sys.path.append("/media/becode/3D_House/")

import BlenderObjectBuilder as bob

import bpy
scene = bpy.context.scene

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

modes = ["ALL", "BLOCK", "SHAPES"]
mode = "ALL"

if mode is "ALL":
    with open("/media/becode/3D_House/object_data.json") as read:
        data = json.load(read)
        for ftype, tif in data.items():
            mesh = bpy.data.meshes.new(ftype)
            mesh.from_pydata(*bob.Grid(tif).data)
            obj = bpy.data.objects.new(ftype, mesh)
            scene.collection.objects.link(obj)
            
if mode is "SHAPES":
    with open("/media/becode/3D_House/object_data.json") as read:
        data = json.load(read)
        for idx, shape in data.items():
            mesh = bpy.data.meshes.new(str(idx))
            mesh.from_pydata(*bob.Ngon(shape).data)
            obj = bpy.data.objects.new(str(idx), mesh)
            bpy.context.scene.collection.objects.link(obj)
            
if mode is "BLOCK":
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