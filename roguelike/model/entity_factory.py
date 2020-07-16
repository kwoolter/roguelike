import tcod as libtcod

def text_to_color(color_text :str)->libtcod.color.Color:
    ''':param:'''

    c = None

    try:
        c = eval(f'libtcod.{color_text.lower()}')
        if isinstance(c, libtcod.color.Color) is False:
            print("We didn't end up with a colour!")
    except AttributeError:
        print("not a valid attribute")

    return c

class Entity():
    def __init__(self, name: str, char: str, x: int = 0, y: int = 0, fg=libtcod.white, bg=None):
        self.name = name
        self.char = char
        self.properties = {}
        self.x = x
        self.y = y
        self.fg=fg
        self.bg=bg

    def __str__(self):
        return f"Name:{self.name}, char:'{self.char}', xy: {self.x}/{self.y}, properties:{self.properties.keys()}"

    @property
    def xy(self):
        return self.x, self.y

    @xy.setter
    def xy(self, new_xy):
        x, y = new_xy
        self.x = x
        self.y = y

    def add_properties(self, new_properties: dict):
        self.properties.update(new_properties)

    def get_property(self, property_name : str):
        return self.properties.get(property_name)

    def move(self, dx: int, dy: int):
        self.x += dx
        self.y += dy


class Player(Entity):
    def __init__(self, name: str, x: int = 0, y: int = 0):
        super().__init__(name=name, char='@', x=x, y=y)


from pathlib import Path
import pandas as pd

class EntityFactory:

    entities = None

    def __init__(self):
        pass

    @staticmethod
    def load(file_name: str):

        # Create path for the file that we are going to load
        data_folder = Path(__file__).resolve().parent
        file_to_open = data_folder / "data" / file_name

        # Read in the csv file
        EntityFactory.entities = pd.read_csv(file_to_open)
        EntityFactory.entities.set_index("Name", drop=True, inplace=True)
        #self.entities.set_index(self.entities.columns[0], drop=True, inplace=True)

        print(EntityFactory.entities.info())

    @staticmethod
    def get_entity_by_name(name: str) -> Entity:
        e = None
        if name in EntityFactory.entities.index:
            row = EntityFactory.entities.loc[name]
            print(row)
            fg = text_to_color(row["FG"])
            bg = text_to_color(row["BG"])
            e = Entity(name=name, char=row["Char"], fg=fg, bg=bg)
            e.add_properties(row.iloc[3:].to_dict())
        else:
            print(f"Can't find entity {name} in factory!")

        return e
            
if __name__ == "__main__":
    ef = EntityFactory()
    ef.load("entities.csv")
    e = ef.get_entity_by_name("rubbish")
    e = ef.get_entity_by_name("Gold")
    print(e)
    property_name = "IsCollectable"
    property_value = e.get_property(property_name)
    if property_value is True:
        print("is true")
    elif property_value == True:
        print("eq True")
    else:
        print("False")
    print(f'{property_name} = {e.get_property(property_name)}')
    print(e.properties)
    