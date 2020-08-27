import pandas as pd
from pathlib import Path
import random


class ThemeManager:

    ROOM_NAMES_BY_THEME = {}
    FLOOR_COLOURS_BY_THEME = {}
    
    room_names = None
    room_palettes = None
    floor_palettes = None
    themes = set()

    def __init__(self):
        pass

    @staticmethod
    def load_room_names(file_name:str):
        # Create path for the file that we are going to load
        data_folder = Path(__file__).resolve().parent
        file_to_open = data_folder / "data" / "themes" / file_name

        # Read in the csv file
        ThemeManager.room_names = pd.read_csv(file_to_open)
        df = ThemeManager.room_names
        df.set_index("Theme", drop=True, inplace=True)

        ThemeManager.themes = ThemeManager.themes.union(set(df.index))

    @staticmethod
    def get_room_names_by_theme(theme_name : str):
        df = ThemeManager.room_names

        assert theme_name in df.index, f'Cannot find {theme_name} in room name index'

        rows = df.loc[theme_name, "Room Name"]
        return list(rows)

    @staticmethod
    def get_random_room_name_by_theme(theme_name:str):
        return random.choice(ThemeManager.get_room_names_by_theme(theme_name))

    @staticmethod
    def load_room_colour_palettes(file_name:str):
        # Create path for the file that we are going to load
        data_folder = Path(__file__).resolve().parent
        file_to_open = data_folder / "data" / "themes" / file_name

        # Read in the csv file
        ThemeManager.room_palettes = pd.read_csv(file_to_open)
        df = ThemeManager.room_palettes
        df.set_index("Theme", drop=True, inplace=True)

        ThemeManager.themes = ThemeManager.themes.union(set(df.index))

    @staticmethod
    def get_room_colours_by_theme(theme_name : str):

        df = ThemeManager.room_palettes

        assert theme_name in df.index, f'Cannot find theme {theme_name} in room colours index'

        rows = df.loc[theme_name,"Room Colour"]
        return list(rows)

    @staticmethod
    def get_random_room_colour_by_theme(theme_name:str):

        return random.choice(ThemeManager.get_room_colours_by_theme(theme_name))

    @staticmethod
    def load_floor_colour_palettes(file_name:str):
        # Create path for the file that we are going to load
        data_folder = Path(__file__).resolve().parent
        file_to_open = data_folder / "data" / "themes" / file_name

        # Read in the csv file
        ThemeManager.floor_palettes = pd.read_csv(file_to_open)
        df = ThemeManager.floor_palettes
        df.set_index("Theme", drop=True, inplace=True)

        ThemeManager.themes = ThemeManager.themes.union(set(df.index))

    @staticmethod
    def get_floor_colours_by_theme(theme_name : str):
        df = ThemeManager.floor_palettes

        assert theme_name in df.index, f'Cannot find {theme_name} in floor colours'

        rows = df.loc[theme_name,"Palette"]
        colours = []
        for colour in rows.split(","):
            colours.append(colour)
        return colours

    @staticmethod
    def get_tunnel_colour_by_theme(theme_name:str):
        return random.choice(ThemeManager.get_floor_colours_by_theme(theme_name))

if __name__ == "__main__":

    ThemeManager.load_room_names("room_names.csv")
    ThemeManager.load_room_colour_palettes("room_palettes.csv")
    ThemeManager.load_floor_colour_palettes("floor_palettes.csv")

    theme = "Desert"
    r = ThemeManager.get_room_names_by_theme(theme)
    print(r)

    r = ThemeManager.get_room_colours_by_theme(theme)
    print(r)

    r = ThemeManager.get_floor_colours_by_theme(theme)
    print(r)

    r = ThemeManager.get_random_room_name_by_theme(theme)
    print(r)

    print(ThemeManager.themes)
    
