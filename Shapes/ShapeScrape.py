import os
import re
import requests
import pandas as pd
from zipfile import ZipFile
from io import StringIO, BytesIO

class NIS:
    def __init__(self,province:str="", place:str="", code:int=0):
        self.province = province
        self.place = place
        self.code = code

    @classmethod
    def from_place(cls, string:str=""):
        for province, places in cls.lookup.items():
            for place, code in places.items():
                if string.lower() == place.lower():
                    return NIS(province, place, code)
        print("No entry found from given string")

    @classmethod
    def from_code(cls, nis_code:int=0):
        for province, places in cls.lookup.items():
            for place, code in places.items():
                if code == nis_code:
                    return NIS(province, place, code)
        print("No entry found from given code")

    @classmethod
    def collection(cls):
        for province, collection in cls.lookup.items():
            for place, code in collection.items():
                yield NIS(province, place, code)

    @classmethod
    def print_lookup(cls):
        for province, collection in cls.lookup.items():
            print(f"{province}\n" + "".join("-" for i in range(len(province))))
            for place, nis in collection.items():
                print(f"{nis} : {place}")
            print("\n")

    def initialize_dictionary():
        url = "https://statbel.fgov.be/sites/default/files/Over_Statbel_FR/Nomenclaturen/REFNIS_DEFINITIEF.csv"
        refnis = pd.read_csv(StringIO(requests.get(url).content.decode("latin1")), sep=";")
        refnis.drop(["Code INS","Entités administratives","Langue"], axis=1, inplace=True)

        result = {}
        province_nis_range = {
            "Antwerpen":       lambda x: 10000 <=x <20000,
            "Brussel":         lambda x: 21000 <=x <22000,
            "Vlaams-Brabant":  lambda x: 22000 <=x <24000,
            "West-Vlaanderen": lambda x: 30000 <=x <40000,
            "Oost-Vlaanderen": lambda x: 40000 <=x <50000,
            "Limburg":         lambda x: 70000 <=x <80000}

        for province, nis_range in province_nis_range.items():
            dataframe = refnis[
                refnis["Code NIS"].apply(nis_range)
               &refnis["Code NIS"].apply(lambda x: x%1000 is not 0)]
            dataframe = dataframe.sort_values("Administratieve eenheden")
            result[province] = dict(zip(
                (item[1] for item in dataframe["Administratieve eenheden"].items()),
                (item[1] for item in dataframe["Code NIS"].items())))
        return result
    lookup = initialize_dictionary()

def get_shapefiles_from_nis_code(data_sets:[], nis:NIS) -> bool:
    url = f"https://eservices.minfin.fgov.be/myminfin-rest/cadastral-plan/cadastralPlan/2020/{nis.code}/72"
    for data_set in data_sets:
        req = requests.get(url).content
        if req is b"": return True
        with ZipFile(BytesIO(req)) as package:
            for content in package.namelist():
                if re.match(f".*({data_set}).*", content):
                    root_dir = f"./{nis.province}/"
                    directory = root_dir + f"{nis.place}/"
                    if not os.path.exists(root_dir): os.mkdir(root_dir)
                    if not os.path.exists(directory): os.mkdir(directory)
                    with open(f"{directory}{content}", "wb") as file:
                        file.write(package.read(content))

if __name__=="__main__":
    import time
    with open("shape_scrape_logs", "w") as logs:
        start_abs = time.time()
        for nis in NIS.collection():
            start = time.time()
            failed = get_shapefiles_from_nis_code(["CaBl","CaBu","ReBu"], nis)
            if failed: log = f"FAILED to download {nis.place} !!!\n"
            else: log = f"Downloaded {nis.place} in {round(time.time() -start, 2)} seconds\n"
            print(log)
            logs.write(log)
        total = round(time.time() -start_abs, 2)
        minutes = total // 60
        seconds = total - minutes *60
        log = f"Finished after {minutes} minutes and {seconds} seconds\n"
        print(log)
        logs.write(log)
