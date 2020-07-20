import json
import requests
import subprocess
import numpy as np
import geopandas as gpd
from dependencies import Box
from dependencies import GeoTIFF
from dependencies import Shape
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon
from BlenderObjectBuilder import Vertex

def get_lambert(address:str) -> (int,int):
    req = requests.get(f"http://loc.geopunt.be/geolocation/location?q={address}&c=1")
    return (req.json()["LocationResult"][0]["Location"]["X_Lambert72"],
            req.json()["LocationResult"][0]["Location"]["Y_Lambert72"])

if __name__=="__main__":
    while True:
        print("\n[ BLOCK, CAD, RAW ]")
        mode = input(" Select a mode : ")
        if mode == "BLOCK":
            x, y = get_lambert(input(" Address : "))            
            ftype = input(" Which shapefile? ")
            print("Cropping terrain map")
            crop_DTM = GeoTIFF.get_containing_tif(x,y,100, "DTM")
            print("Cropping surface map")
            crop_DSM = GeoTIFF.get_containing_tif(x,y,100, "DSM")
            print("Loading shapefile")
            file = Shape.get_containing_shape_file(crop_DTM.box, ftype)
            print("Getting shapes in crop")
            shapes = Shape.get_shapes_in_box(file, crop_DTM.box)
            print("Normalizing")
            normalized_origin = Vertex(crop_DTM.box.left, crop_DSM.box.bottom)
            print("Generating terrain data")
            terrain = {}
            for idx, y in enumerate(range(crop_DTM.arr.shape[0])[::-1]):
                terrain[idx] = []
                for x in range(crop_DTM.arr.shape[1]):
                    terrain[idx].append(np.float64(crop_DTM.arr[y,x]))
            print("Generating building blocks")
            blocks = {idx : {
                "vertices": list(map(lambda x: (x -normalized_origin).xyz, Shape.polygon_to_vertices(entry))),
                "height": np.float64(Shape.mean_shape_height(crop_DSM, entry) +1)}
                    for idx, entry in shapes.geometry.iteritems()}
            print("Combining data")
            data = {"terrain": terrain, "blocks": blocks}
        
        if mode == "CAD":
            province = input(" Which province? ")
            place = input(" Plot what place? ")
            file = input(" Which shapefile? ")
            
            print("Loading shapefile")
            shapes = gpd.read_file(f"/media/becode/3D_House/Shapes/{province}/{place}/Bpn_{file}.shp")
            minx = shapes.bounds.minx.min()
            miny = shapes.bounds.miny.min()
            normalized_origin = Vertex(minx, miny)
            
            print("Creating data")
            data = {idx : Shape.polygon_to_vertices(entry)
                    for idx, entry in shapes.geometry[
                        shapes.geometry.apply(lambda x: type(x) != MultiPolygon)
                    ].iteritems()}
            
            for idx, shape in data.items():
                for i, vertex in enumerate(shape):
                    data[idx][i] = (vertex -normalized_origin).scale(10).xyz

        if mode == "RAW":
            x, y = get_lambert(input(" Address : "))
            print("Loading surface map")
            DSM = GeoTIFF.get_tif_from_point(x,y, "DSM").arr
            print("Loading terrain map")
            DTM = GeoTIFF.get_tif_from_point(x,y, "DTM").arr            
            print("Creating canopy map")
            tifs = {"DSM": DSM, "DTM": DTM, "DCM": DSM - DTM}
            
            print("Creating data")
            data = {}
            for ftype, tif in tifs.items():
                data[ftype] = {}
                for y in range(tif.shape[0]):
                    data[ftype][y] = []
                    for x in range(tif.shape[1]):
                        data[ftype][y].append(np.float64(tif[y,x]))
                    data[ftype][y] = data[ftype][y][::-1]   
        
        print("Dumping json data")
        with open("./object_data.json", "w") as out:
                json.dump(data, out)
        print("Injecting blender")
        subprocess.run(f"blender -P blender_inject_{mode}.py", shell=True)