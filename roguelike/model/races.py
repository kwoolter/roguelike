import pandas as pd
from pathlib import Path
import logging

class Race:
    def __init__(self, name:str):
        self.name = name
        self.properties = {}

    def add_properties(self, new_properties: dict):
        self.properties.update(new_properties)

    def __str__(self):
        text =f'{self.name}:'
        for k,v in self.properties.items():
            text+=f'{k}={v},'

        return text

class RaceFactory:

    races = None

    def __init__(self):
        pass

    @staticmethod
    def load(file_name: str):

        # Create path for the file that we are going to load
        data_folder = Path(__file__).resolve().parent
        file_to_open = data_folder / "data" / file_name

        # Read in the csv file
        RaceFactory.races = pd.read_csv(file_to_open)
        RaceFactory.races.set_index("Race", drop=True, inplace=True)

        print(RaceFactory.races.tail(10))

    @staticmethod
    def get_available_races()->list:
        return list(RaceFactory.races.index)

    @staticmethod
    def get_race_by_name(name: str) -> Race:
        races = RaceFactory.races
        e = None
        if name in list(races.index):
            row = races.loc[name]
            e = Race(name)
            e.add_properties(row.iloc[:].to_dict())

        else:
            logging.warning(f"Can't find race {name} in factory!")

        return e

if __name__ == "__main__":

    RaceFactory.load("races.csv")

    names = RaceFactory.get_available_races()
    for name in names:
        r = RaceFactory.get_race_by_name(name)
        print(r)
