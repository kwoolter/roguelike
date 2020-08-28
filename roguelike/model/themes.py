import pandas as pd
from pathlib import Path
import random
import tcod as libtcod

class Palette:

    def __init__(self, name:str):
        self.name = name
        self.colour_mappings = {}

    def add_colours(self, new_colours:dict):

        # Convery all of the text representation of the new colours to Color objects
        new_colour_rgb = {k:Palette.text_to_color(v) for k,v in new_colours.items()}

        # Add/update the new colours to this Palette
        self.colour_mappings.update(new_colour_rgb)

    def get(self, property_name: str):
        return self.colour_mappings.get(property_name)

    def dim(self, pct):
        """
        Dim all of the colours in the palette
        :param pct: Percentage that you want to dim them by
        """
        self.colour_mappings = {k: Palette.dim_rgb_pct(v,pct) for k,v in self.colour_mappings.items()}

    @staticmethod
    def text_to_color(color_text: str) -> libtcod.color.Color:
        """
        Convert a libtcod text representation of a colour to a Color object
        :param color_text: the text that specifies the colour e.g. 'red'
        :return: the Color object that represents the colour specified by the text
        """
        try:
            c = eval(f'libtcod.{color_text.lower()}')
            if isinstance(c, libtcod.color.Color) is False:
                print(f"We didn't end up with a colour from text {color_text}!")
                c = None
        except AttributeError:
            # print(f"{color_text} is not a valid attribute")
            c = None

        return c

    @staticmethod
    def dim_rgb(rgb, dc: int):
        """
        Dim a colour by a specified amount
        :param rgb: the RGB colour that you want to dim
        :param dc: how much do you want to dim it by?
        :return: a libtcod.Color object with the dimmed RGB colour
        """
        r, g, b = rgb
        r = min(max(0, r - dc), 255)
        g = min(max(0, g - dc), 255)
        b = min(max(0, b - dc), 255)
        return libtcod.Color(r, g, b)

    @staticmethod
    def dim_rgb_pct(rgb, pct: float) -> libtcod.Color:
        """
        Dim a colour by a specified amount
        :param rgb: the RGB colour that you want to dim
        :param pct: how much do you want to dim it by as a percentage?
        :return: a libtcod.Color object with the dimmed RGB colour
        """
        r, g, b = rgb
        r = int(min(max(0, r * pct), 255))
        g = int(min(max(0, g * pct), 255))
        b = int(min(max(0, b * pct), 255))

        return libtcod.Color(r, g, b)

    @staticmethod
    def dim_hsl(colour, amt : int):

        return libtcod.color_scale_HSV(colour,1.0,amt)


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

        dimmed_colours = []
        for colour_text in list(rows):
            colour = Palette.text_to_color(colour_text)
            dimmed_colours.append(Palette.dim_rgb_pct(colour, 0.8))
        return dimmed_colours

    @staticmethod
    def get_random_room_colour_by_theme(theme_name:str):

        assert theme_name in ThemeManager.room_palettes.index, f'{theme_name} not in room colour themes'

        print(ThemeManager.get_room_colours_by_theme(theme_name))

        return random.choice(ThemeManager.get_room_colours_by_theme(theme_name))

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
    def get_floor_palette_by_theme(theme_name : str):
        df = ThemeManager.floor_palettes

        assert theme_name in df.index, f'Cannot find {theme_name} in floor colours'

        row = df.loc[theme_name]

        palette = Palette(name=theme_name)
        palette.add_colours(row.to_dict())
        palette.dim(0.6)

        return palette

    @staticmethod
    def get_tunnel_colours_by_theme(theme_name:str):

        df = ThemeManager.floor_palettes

        assert theme_name in df.index, f'Cannot find {theme_name} in floor palettes'

        # Get the floor palette for the specified theme
        row = df.loc[theme_name]

        palette = Palette(name=theme_name)
        palette.add_colours(row.to_dict())
        bg_tunnel = palette.get("BG_TUNNEL")

        valid_tunnel_colours = [bg_tunnel]

        for i in range(10):
            # Make the colour even darker!
            bg_tunnel = Palette.dim_rgb_pct(list(bg_tunnel), 0.95)
            valid_tunnel_colours.append(bg_tunnel)

        #print(valid_tunnel_colours)

        return valid_tunnel_colours

if __name__ == "__main__":

    ThemeManager.load_room_names("room_names.csv")
    ThemeManager.load_room_colour_palettes("room_palettes.csv")
    ThemeManager.load_floor_colour_palettes("floor_palettes.csv")

    theme = "Desert"

    r = ThemeManager.get_room_colours_by_theme(theme)
    print(r)

    r = ThemeManager.get_random_room_name_by_theme(theme)
    print(r)

    r = ThemeManager.get_floor_palette_by_theme(theme)
    print(str(r.colour_mappings))


    r = ThemeManager.get_tunnel_colours_by_theme(theme)
    print(r)

    print(ThemeManager.themes)
    
