import pandas as pd
from pathlib import Path
import random
import tcod as libtcod
import copy
import textwrap

class Palette:
    """
    Class for holding the palette of colours for various features on a Floor
    """

    def __init__(self, name:str):
        self.name = name
        self.colour_mappings = {}

    def add_colours(self, new_colours:dict):
        """
        As a dictionary of floor features to colours to this Palette.
        The colours must be in the list of pre-defined libtcod colours e.g. "red", "blue"
        :param new_colours: the new colours that you want to add.  Format is feature:colour text e.f. "FG":"red"
        """

        # Check to make sure all of the new colours exist
        for c in new_colours.values():
            assert Palette.text_to_color(c) is not None, f'Do not know colour {c}'

        # Convert all of the text representation of the new colours to Color objects
        new_colour_rgb = {k:Palette.text_to_color(v) for k,v in new_colours.items() if Palette.text_to_color(v) is not None}

        # Add/update the new colours to this Palette
        self.colour_mappings.update(new_colour_rgb)

    def get(self, property_name: str):
        """
        Get the colour for a specified Floor property
        :param property_name: the property that you want the colour for e.g. "FG"
        :return: the Color object that the property maps to
        """
        return self.colour_mappings.get(property_name)

    def dim(self, pct):
        """
        Dim all of the colours in the palette by asjusting L value of HSL representation
        :param pct: Percentage that you want to dim them by
        """
        self.colour_mappings = {k: self.dim_hsl(v,pct) for k, v in self.colour_mappings.items()}


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
        """
        Dim a colour object by adjusting the L attribute of HSL representation
        :param colour: the colour that you want to adjust
        :param amt: the coefficient you want to adjust it by. 1.0 means unchanged
        :return: the new colour
        """
        new_colour = copy.deepcopy(colour)
        libtcod.color_scale_HSV(new_colour, 1.0, amt)
        return new_colour


class ThemeManager:

    ROOM_COLOUR_DIM_COEF = 0.65
    FLOOR_COLOUR_DIM_COEF = 0.6
    TUNNEL_COLOUR_DIM_COEF = 0.9

    room_names = None
    room_palettes = None
    floor_palettes = None
    available_themes = set()

    def __init__(self):
        pass

    @staticmethod
    def load_room_names(file_name:str):
        """
        Load in the contents of a specified csv file containing Room names by theme
        Args:
            file_name: the file that you want to load
        """
        # Create path for the file that we are going to load
        data_folder = Path(__file__).resolve().parent
        file_to_open = data_folder / "data" / "themes" / file_name

        # Read in the csv file
        ThemeManager.room_names = pd.read_csv(file_to_open)
        df = ThemeManager.room_names
        df.set_index("Theme", drop=True, inplace=True)

        # Add the themes that we found in the file to the set of available themes
        ThemeManager.available_themes = ThemeManager.available_themes.union(set(df.index))

    @staticmethod
    def get_room_names_by_theme(theme_name : str)->list:
        """
        Return a list of available Room names given a specified theme name
        Args:
            theme_name: the name of the theme that you are interested in

        Returns: the list of available Room names that we found

        """
        df = ThemeManager.room_names

        assert theme_name in df.index, f'Cannot find {theme_name} in room name index'

        rows = df.loc[theme_name, "Room Name"]
        return list(rows)

    @staticmethod
    def get_random_room_name_by_theme(theme_name:str)->str:
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

        # Add the themes that we found in the file to the set of available themes
        ThemeManager.available_themes = ThemeManager.available_themes.union(set(df.index))

    @staticmethod
    def load_history_data(file_name:str):
        """
        Use libtcod library to load in the name generation configuration
        :param file_name: the name of the config file that you want to load
        """
        # Create path for the file that we are going to load
        data_folder = Path(__file__).resolve().parent
        file_to_open = data_folder / "data" / "themes" / file_name

        libtcod.namegen_parse(str(file_to_open))


    @staticmethod
    def get_random_history(theme:str)->str:
        """
        A method for generating some random Lore based on the specified theme
        :param theme: the theme of Lore that you want to generate e.g. Room, Person
        :return: a string with the generated name
        """

        # Templates for generating different types of Lore themes
        templates = {
            "Room":(["Dungeon Rooms"],None),
            "Floor": (["Dungeon Floors"], [" of "], ["Historic Figure Names Male","Historic Figure Names Female","Region", "Town"]),
            "Place":(["Town","Wonders"],[" in "],["Region"]),
            "Person":(["Character Male", "Character Female", "Fantasy Male","Fantasy Female"],[" of "],["Town","Region","Wonders","Place"]),
            "Quest":(["Historic Figure Names Male", "Historic Figure Names Female"],
                     [" and the battle of "," and the Siege of "," and the Quest for "," and the journey to ",
                      " and the destruction of "," and the decimation of "," and how they found ",
                      " and how they discovered "],
                     ["Town", "Region", "Treasures", "Wonders", "Place"]),
            "PvP":(["Historic Figure Names Male","Historic Figure Names Female","Person"],
                   [" and the murder of "," and the death of "," and the unmarriage of "," and the betrayal of ",
                    " and the hunt for "," and the alliance with "," and the usurping of "," and the torment of ",
                    ", the loyal servant of ", ", the sworn enemy of "],
                   ["Historic Figure Names Male","Historic Figure Names Female", "Person"]),
            "Treasure":(["Treasures"],[" of "],["Historic Figure Names Male","Historic Figure Names Female","Region","Town","Wonders" ]),
            "Book":(["'"],
                    ["The missing pages of ","The forgotten passages of ","The ancient Lore of ", "The lessons of ",
                     "A cautionary tale of ", "The Tale of ","The Saga of ","An allegory of ","The writings of ",
                     "The story of ","The book of "],
                    ["Quest", "Place", "Historic Figure Names Male","Historic Figure Names Female", "Treasure","PvP"],
                    ["'"],
                    [" by "],
                    ["Person"])
        }


        assert theme in templates, f'Cannot find {theme} in history templates'

        # See what name generate sets we have loaded
        ng_sets = libtcod.namegen_get_sets()

        # Get the name of the template that we want to expand
        template = templates.get(theme)

        text = ""

        # Loop through each segment in the template
        for aa in template:

            # If None segment keep looping to the next one
            if aa is None:
                continue
            # Otherwise...
            else:
                # Pick a random item from the segment
                a = random.choice(aa)

                # If the segment a template?  If so recursive call to expand the template
                if a in templates:
                    a_text = ThemeManager.get_random_history(a)
                # If it is in out name generation sets that we loaded then generate a name of this type
                elif a in ng_sets:
                    a_text = libtcod.namegen_generate(a).title()
                # Else just use the segment text itself!
                else:
                    a_text=a

                # Add whatever text we ended up with to our full text
                text += a_text

        # Tidy up by removing any duplicate whitespace
        return " ".join(text.split())


    @staticmethod
    def get_room_colours_by_theme(theme_name : str)->list:
        """
        Get the list of Room colours for the specified theme
        Args:
            theme_name: the name of the theme that you are interested in

        Returns: the list of colours that we found

        """
        df = ThemeManager.room_palettes

        assert theme_name in df.index, f'Cannot find theme {theme_name} in room colours index'

        rows = df.loc[theme_name,"Room Colour"]

        # Build a list of colours based on those we loaded in but each one is dimmed
        dimmed_colours = []
        for colour_text in list(rows):
            colour = Palette.text_to_color(colour_text)
            dimmed_colours.append(Palette.dim_hsl(colour, ThemeManager.ROOM_COLOUR_DIM_COEF))

        return dimmed_colours

    @staticmethod
    def get_random_room_colour_by_theme(theme_name:str):

        assert theme_name in ThemeManager.room_palettes.index, f'{theme_name} not in room colour themes'

        return random.choice(ThemeManager.get_room_colours_by_theme(theme_name))

    def load_floor_colour_palettes(file_name:str):
        # Create path for the file that we are going to load
        data_folder = Path(__file__).resolve().parent
        file_to_open = data_folder / "data" / "themes" / file_name

        # Read in the csv file
        ThemeManager.floor_palettes = pd.read_csv(file_to_open)
        df = ThemeManager.floor_palettes
        df.set_index("Theme", drop=True, inplace=True)

        ThemeManager.available_themes = ThemeManager.available_themes.union(set(df.index))

    @staticmethod
    def get_floor_palette_by_theme(theme_name : str)->Palette:
        """
        Create Palette object for the specified theme name
        Args:
            theme_name: the name of the theme that you are interested in

        Returns: a Palette object containing the colours for the specified theme

        """
        df = ThemeManager.floor_palettes

        assert theme_name in df.index, f'Cannot find {theme_name} in floor colours'

        row = df.loc[theme_name]

        palette = Palette(name=theme_name)
        palette.add_colours(row.to_dict())

        # Dim all of the colours in the Palette by a coefficient
        palette.dim(ThemeManager.FLOOR_COLOUR_DIM_COEF)

        return palette

    @staticmethod
    def get_tunnel_colours_by_theme(theme_name:str, k:int = 10):
        """
        Create a list of colours for tunnels starting with a base colour that we get from the Floor palette
        for the specified theme and then dimming it
        Args:
            theme_name: the theme we want to use as a base
            k: how many colours do we want to generate

        Returns:list of generated colours

        """
        # Get the floor palette for the specified theme
        palette = ThemeManager.get_floor_palette_by_theme(theme_name)
        bg_tunnel = palette.get("BG_TUNNEL")

        # Start building a list of valid tunnel colours
        valid_tunnel_colours = [bg_tunnel]

        # Create k more colours by dimming the original by a specified coefficient
        for i in range(k):
            # Make the colour even darker!
            bg_tunnel = Palette.dim_hsl(bg_tunnel, ThemeManager.TUNNEL_COLOUR_DIM_COEF)
            valid_tunnel_colours.append(bg_tunnel)

        return valid_tunnel_colours

if __name__ == "__main__":

    ThemeManager.load_room_names("room_names.csv")
    ThemeManager.load_room_colour_palettes("room_palettes.csv")
    ThemeManager.load_floor_colour_palettes("floor_palettes.csv")
    ThemeManager.load_history_data("rogue_history.cfg")

    theme = "Desert"

    things = ["Floor","Room","Place","Person", "Quest","Treasure", "Book","PvP"]

    for thing in things:
        print(f'\n{thing:=^60}')
        for i in range(10):
            r = ThemeManager.get_random_history(thing)
            print(r)
    assert False


    r = ThemeManager.get_room_colours_by_theme(theme)
    print(r)

    r = ThemeManager.get_random_room_name_by_theme(theme)
    print(r)

    r = ThemeManager.get_floor_palette_by_theme(theme)
    print(str(r.colour_mappings))


    r = ThemeManager.get_tunnel_colours_by_theme(theme)
    print(r)

    print(ThemeManager.available_themes)
    
