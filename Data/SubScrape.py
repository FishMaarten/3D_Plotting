import os
import re
import time
import requests
import numpy as np
import pandas as pd
import rasterio as rio
from io import BytesIO
from zipfile import ZipFile
from dependencies import Box
from rasterio import MemoryFile
from rasterio.plot import show
from rasterio.transform import from_bounds 
from bs4 import BeautifulSoup as BS

def timerlog(func):
    def time_elapsed(*args):
        with open("subscrape_logs", "a") as out:
            logit(out,f"Starting {func.__name__}{args}\n")
            start = time.time()
            ret = func(*args)
            total = round(time.time() - start, 5)
            logit(out, f"Finished {func.__name__}{args} {total}seconds\n")
            return ret
    def logit(out, message:str=""):
        out.write(message)
        print(message)
    return time_elapsed

class SubScrape:
    def __init__(self, url:str, tif_type:str):
        self.url = url
        self.tif_type = tif_type

    @timerlog
    def start_root_division(self):
        data = self.tif_data_from_zip_url(self.url)
        directory = f"./{data[0]}/"
        if not os.path.exists(directory):
            os.mkdir(directory)
        self.subdivide(data[0], "", data[1:])

    @timerlog
    def tif_data_from_zip_url(self, url:str) -> (np.array, Box, {}):
        req = requests.get(url)
        with ZipFile(BytesIO(req.content)) as package:
            for contents in package.namelist():
                if (re.match(r".*\.tif$", contents)):
                    root = re.findall(r"k[0-9]{2}",contents)[0]
                    with MemoryFile(package.open(contents)) as memfile:
                        with memfile.open() as dataset:
                            return root, np.array(dataset.read(1)), Box(dataset.bounds), dataset.meta
    @timerlog
    def subdivide(self, root:str="", name:str="", tif:rio.io.DatasetReader=(), sub:int=5) -> None:
        if sub is 0: return
        if type(tif) == tuple:
            arr, box, meta = tif
            #with open("./data_lookup.csv", "a") as csv:
            #    csv.write("|".join((root,"ROOT", repr(box))) +"\n")
        else: arr, box, meta = np.array(tif.read(1)), Box(tif.bounds), tif.meta 
        
        width = meta["width"] = box.width /2
        height = meta["height"] = box.height /2
        sub_bound = {0:(0,1,-1,0), 1:(1,1,0,0), 2:(0,0,-1,-1), 3:(1,0,0,-1)}
        sub_slice = {
            0:{"sx":slice(None,int(height)),
               "sy":slice(None,int(width))},
            1:{"sx":slice(None,int(height)),
               "sy":slice(int(width),None)},
            2:{"sx":slice(int(height),None),
               "sy":slice(None,int(width))},
            3:{"sx":slice(int(height),None),
               "sy":slice(int(width),None)}}
        for idx in range(4):
            sub_name = name + (str(idx) if name is "" else f"_{idx}")
            directory = f"./{root}/{sub_name}/"
            if not os.path.exists(directory): os.mkdir(directory)

            meta["transform"] = from_bounds(
                box.left + width * sub_bound[idx][0],
                box.bottom + height * sub_bound[idx][1],
                box.right + width * sub_bound[idx][2],
                box.top + height * sub_bound[idx][3],
                width, height)

            with rio.open(directory +f"{self.tif_type}.tif", "w+", **meta) as sub_tif:
                sub_tif.write(arr[sub_slice[idx]["sx"], sub_slice[idx]["sy"]], indexes=1)
                self.subdivide(root, sub_name, sub_tif, sub -1)
                if sub > 1:
                    os.remove(directory +f"{self.tif_type}.tif")
                    os.rmdir(directory)
                    continue
                #with open("./data_lookup.csv", "a") as csv:
                #    csv.write("|".join((root, sub_name, repr(Box(sub_tif.bounds)), directory +"DSM.tif")) +"\n")

DSM_url = "http://www.geopunt.be/download?container=dhm-vlaanderen-ii-dsm-raster-1m"
DSM_url += "&title=Digitaal%20Hoogtemodel%20Vlaanderen%20II,%20DSM,%20raster,%201m"
DTM_url = "http://www.geopunt.be/download?container=dhm-vlaanderen-ii-dtm-raster-1m"
DTM_url += "&title=Digitaal%20Hoogtemodel%20Vlaanderen%20II,%20DTM,%20raster,%201m"

@timerlog
def zip_url_list(zip_collection_url) -> [str]:
    soup = BS(requests.get(zip_collection_url).content, "lxml")
    scrape_list_raw = [ele.get("href") for ele in soup.find_all("a")]
    return [url for url in scrape_list_raw if re.match(r"^http", url)]

@timerlog
def divide_and_conquer():
    if not os.path.exists("./data_lookup.csv"):
        with open("./data_lookup.csv", "w") as csv:
            csv.write("|".join(("ROOT","PATH","BOX","DSM","DTM","SHP")) +"\n")
    for zip_url in zip_url_list(DTM_url):
        subscrape = SubScrape(zip_url, "DTM")
        subscrape.start_root_division()

if __name__=="__main__":
    divide_and_conquer()
