import io
import numpy as np
import pandas as pd
import rasterio as rio
import geopandas as gpd
from geopandas import GeoDataFrame
from rasterio.plot import show
from rasterio import DatasetReader
from rasterio.mask import mask
from rasterio.transform import from_bounds
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon
from BlenderObjectBuilder import Vertex

class Box:
    def __init__(self, bounds=None, left:int=0, bottom:int=0, right:int=0, top:int=0):
        if bounds is not None: self.left, self.bottom, self.right, self.top = bounds
        else: self.left, self.bottom, self.right, self.top = left, bottom, right, top
        self.width, self.height = self.right -self.left, self.top -self.bottom
        
    def __str__(self):
        return "left:{} bottom:{} right:{} top:{} width:{} height:{}".format(
            self.left, self.bottom, self.right, self.top, self.width, self.height)
    def __repr__(self):
        return "{} {} {} {} {} {}".format(
            str(int(self.left)),  str(int(self.bottom)),
            str(int(self.right)), str(int(self.top)),
            str(int(self.width)), str(int(self.height)))
    def contains_point(self, x:int, y:int) -> bool:
        return self.left <= x < self.right and self.bottom <= y < self.top
    def contains_box(self, other) -> bool:
        return (other.left >= self.left and other.bottom >= self.bottom 
            and other.right <= self.right and other.top <= self.top)
    
    @classmethod
    def around_point(cls, x:int, y:int, size:int):
        return Box(None, x-size/2, y-size/2, x+size/2, y+size/2)
    @classmethod
    def from_string(cls, string:str=""):
        string = string.split(" ")
        return Box(
            None, int(string[0]), int(string[1]), int(string[2]), int(string[3]))    

class GeoTIFF:
    def __init__(self, tif_path:str):
        self.tif_path = tif_path
        with rio.open(tif_path) as tif:
            self.arr = tif.read(1)
            self.box = Box(tif.bounds)
            self.meta = tif.meta
            
    def load(self) -> DatasetReader: return rio.open(self.tif_path)
    def show(self, cmap:str="cividis"): return show(self.load(), cmap=cmap)
    
    def get_neighbour(self, direction:str):
        point = {"left": (self.box.left -10, self.box.top -self.box.height/2),
                 "bottom": (self.box.right -self.box.width/2, self.box.bottom -10),
                 "right": (self.box.right +10, self.box.top -self.box.height/2),
                 "top": (self.box.right -self.box.width/2, self.box.top +10)}
        return GeoTIFF(get_tif_from_point(*point[direction]))
    
    def crop_location(self, x:float, y:float, width:int=100, height:int=100):
        posx, posy = int(x -self.box.left), int(abs(y -self.box.top))
        slicex = slice(posx -width//2, posx +width//2)
        slicey = slice(posy -height//2, posy +height//2)        
        meta = self.meta
        meta["width"], meta["height"] = width, height
        meta["transform"] = from_bounds(
            self.box.left + slicex.start,
            self.box.top - slicey.stop,
            self.box.left + slicex.stop,
            self.box.top - slicey.start,
            width, height)
        # USE MEMFILE
        with rio.open("./crop.tif", "w", **meta) as crop:
            crop.write(self.arr[slicey,slicex], indexes=1)
        return GeoTIFF("./crop.tif")
     
    @classmethod
    def get_root_from_point(cls, x:int, y:int) -> str:
        return root[root.BOX.apply(lambda b:Box.from_string(b).contains_point(x,y))].ROOT.values[0]
    
    @classmethod
    def get_sub_from_point(cls, x:int, y:int) -> str:
        df = data_lookup[(data_lookup.ROOT == cls.get_root_from_point(x,y)) & (data_lookup.PATH != "ROOT")]
        return df[df.BOX.apply(lambda b:Box.from_string(b).contains_point(x,y))].PATH.values[0]
    
    @classmethod
    def get_tif_from_point(cls, x:int, y:int, ftype:str):
        df = data_lookup[(data_lookup.ROOT == cls.get_root_from_point(x,y)) & (data_lookup.PATH != "ROOT")]
        return GeoTIFF(df[df.BOX.apply(lambda b:Box.from_string(b).contains_point(x,y))][ftype].values[0])
    
    @classmethod
    def get_containing_tif(cls, x:int, y:int, size:int=100, ftype:str="DSM"):
        main = cls.get_tif_from_point(x,y,ftype)
        main_box = main.box
        crop_box = Box.around_point(x,y,size)
        if main_box.contains_box(crop_box): return main

        result = {}
        if crop_box.left < main_box.left: result["left"]  = cls.get_tif_from_point(crop_box.left, y, ftype)
        if crop_box.bottom < main_box.bottom: result["bottom"]  = cls.get_tif_from_point(x, crop_box.bottom, ftype)
        if crop_box.right > main_box.right: result["right"]  = cls.get_tif_from_point(crop_box.right, y, ftype)
        if crop_box.top > main_box.top: result["top"]  = cls.get_tif_from_point(x, crop_box.top, ftype)
        # TEMP SOLUTION
        for k, v in result.items():
            return cls.concat_tifs((main, v), k)
    
    @classmethod
    def concat_tifs(cls, tifs:(), key:str):
        meta = tifs[0].meta
        meta["width"] *= 2 if key is "left" or key is "right" else 1
        meta["height"] *= 2 if key is "bottom" or key is "top" else 1
        meta["transform"] = from_bounds(
            tifs[cls.align[key][0]].box.left,
            tifs[cls.align[key][1]].box.bottom,
            tifs[cls.align[key][1]].box.right,
            tifs[cls.align[key][0]].box.top,
            meta["width"], meta["height"])
        arr = np.concatenate((
            np.array(tifs[cls.align[key][0]].arr),
            np.array(tifs[cls.align[key][1]].arr)),
            axis= cls.align[key][2])
        # USE MEMFILE
        with rio.open("./temp.tif", "w", **meta) as temp:
            temp.write(arr, indexes=1)
        return GeoTIFF("./temp.tif")
    align = {"left": (1,0,1),"bottom": (0,1,0),"right": (0,1,1),"top": (1,0,0)}
    
    
data_lookup = pd.read_csv("/media/becode/3D_House/Data/data_lookup.csv", sep="|")
root = data_lookup[data_lookup.PATH == "ROOT"]

class Shape:
    @classmethod
    def poly_coord_to_vertex(cls, coord:(float,float)) -> Vertex:
        return Vertex(*coord)
    @classmethod
    def polygon_to_vertices(cls, poly:Polygon) -> [Vertex]:
        result = []
        for coord in poly.exterior.coords:
            result.append(cls.poly_coord_to_vertex(coord))
        return result[:-1]
    @classmethod
    def center(cls, poly:Polygon):
        return(int(poly.bounds[0]+poly.bounds[2]-poly.bounds[0]),
               int(poly.bounds[1]+poly.bounds[3]-poly.bounds[1]))
    @classmethod
    def mean_shape_height(cls, tif, shape):
        out_image, out_transform = mask(tif.load(), shapes=[shape], crop=True, invert=False)
        li = []
        for y in out_image[0]:
            for x in y:
                if x > 0: li.append(x)
        return np.array(li).mean()
    @classmethod
    def get_shape_entry_from_point(cls, x:float, y:float):
        return shape_lookup[shape_lookup.CaBl.apply(lambda s: Box.from_string(s).contains_point(x,y) == True)]
    @classmethod
    def get_shape_file_from_point(cls, x:float, y:float, ftype:str):
        entry = cls.get_shape_entry_from_point(x,y)
        return gpd.read_file(f"./Shapes/{entry.Province.values[0]}/{entry.Place.values[0]}/Bpn_{ftype}.shp")
    @classmethod
    def get_containing_shape_file(cls, tif_box:Box, ftype:str):
        entry = shape_lookup[shape_lookup[ftype].apply(
            lambda x:Box.from_string(x).contains_box(tif_box) if pd.notnull(x) else False)]
        if entry.empty: return False
        return gpd.read_file(f"./Shapes/{entry.Province.values[0]}/{entry.Place.values[0]}/Bpn_{ftype}.shp")
    @classmethod
    def get_shapes_in_box(cls, gdf: GeoDataFrame, box: Box) -> GeoDataFrame:
        return gdf[gdf.geometry.apply(
            lambda d: box.contains_point(
                x = cls.center(Polygon(d))[0],
                y = cls.center(Polygon(d))[1])
            if type(d) != MultiPolygon else False)]
shape_lookup = pd.read_csv("/media/becode/3D_House/Shapes/shape_lookup.csv", sep="|")