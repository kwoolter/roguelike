import tcod as libtcod
from .combat import *

def text_to_color(color_text :str)->libtcod.color.Color:
    ''':param:'''

    try:
        c = eval(f'libtcod.{color_text.lower()}')
        if isinstance(c, libtcod.color.Color) is False:
            print("We didn't end up with a colour!")
            c = None
    except AttributeError:
        print(f"{color_text} is not a valid attribute")
        c = None

    return c

class Entity():

    STATE_INERT = "inert"
    STATE_ALIVE = "alive"
    STATE_DEAD = "dead"

    def __init__(self, name: str,
                 description:str,
                 char: str,
                 x: int = 0, y: int = 0,
                 fg=libtcod.white, bg=None,
                 state = STATE_INERT):

        # Properties
        self.name = name
        self.description = description
        self.char = char
        self._state = state

        self.properties = {}

        self.x = x
        self.y = y
        self.fg=fg
        self.bg=bg

        # Components
        self.inventory = None
        self.fighter = None
        self.combat_equipment = None

    def __str__(self):
        return f"Name:{self.name}, char:'{self.char}', xy: {self.x}/{self.y}, properties:{self.properties.keys()}"

    @property
    def state(self):
        state = self._state
        return state

    @state.setter
    def state(self, new_state):
        self._state = new_state

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
        if self.get_property("IsEnemy") is True:
            self._state = Entity.STATE_ALIVE

    def get_property(self, property_name : str):
        return self.properties.get(property_name) == True

    def move(self, dx: int, dy: int):
        self.x += dx
        self.y += dy


class Player(Entity):
    def __init__(self, name: str, x: int = 0, y: int = 0):
        super().__init__(name=name, description="The player", char='@', x=x, y=y)
        self.inventory = Inventory()

    def equip_item(self, new_item : Entity)->bool:
        success = False
        if new_item.get_property("IsEquipable") == True:
            old_item = self.fighter.equip_item(new_item)
            self.inventory.remove_item(new_item)
            if old_item is not None:
                self.inventory.add_item(old_item)
            success=True
        else:
            print(f"{new_item.name} is not equipable")

        return success

    def drop_item(self, old_item : Entity)->bool:
        return self.inventory.remove_item(old_item)


class Fighter():
    DEFAULT_WEAPON = None
    DEFAULT_WEAPON_NAME = "Hands"
    WEAPON_SLOT = "Right Hand"

    def __init__(self, combat_class: CombatClass):
        self.combat_class = combat_class
        self.equipment = {}
        Fighter.DEFAULT_WEAPON = EntityFactory.get_entity_by_name(Fighter.DEFAULT_WEAPON_NAME)

    @property
    def is_dead(self) -> bool:
        return self.combat_class.get_property("HP") < 0

    @property
    def current_weapon(self) -> Entity:
        eq = self.equipment.get(Fighter.WEAPON_SLOT)
        if eq is None:
            eq = Fighter.DEFAULT_WEAPON
        return eq

    def take_damage(self, damage_amount: int):
        self.combat_class.update_property("HP", damage_amount * -1, increment=True)

    def heal(self, heal_amount: int):
        new_hp = min(self.combat_class.get_property("HP") + heal_amount, self.combat_class.get_property("MAX_HP"))
        self.combat_class.update_property("HP", new_hp)

    def add_XP(self, xp_amount: int):
        self.combat_class.update_property("XP", xp_amount, increment=True)

    def add_kills(self, kill_count: int = 1):
        self.combat_class.update_property("KILLS", kill_count, increment=True)

    def equip_item(self, new_item: Entity) -> Entity:
        new_eq = CombatEquipmentFactory.get_equipment_by_name(new_item.name)
        existing_item = self.equipment.get(new_eq.slot)
        self.equipment[new_eq.slot] = new_item
        return existing_item

    def roll_damage(self) -> int:
        dmg = CombatEquipmentFactory.get_damage_roll_by_name(self.current_weapon.name)
        return dmg

    def get_XP_reward(self)->int:
        reward = random.randint(1, 3)
        return reward

    def print(self):
        print(f'Fighter ({self.combat_class.name})')
        for k, v in self.combat_class.properties.items():
            print(f'\t{k}={v}')
        print("Equipment:")
        for k, v in self.equipment.items():
            print(f'\t{k}={str(v)}')


if __name__ == "__main__":
    CombatClassFactory.load("combat_classes.csv")
    CombatEquipmentFactory.load("combat_equipment.csv")

    cl = CombatClassFactory.get_combat_class_by_name("Warrior")

    f = Fighter(combat_class=cl)

    eq = CombatEquipmentFactory.get_equipment_by_name("Sword")
    f.equip_item(eq)
    eq = CombatEquipmentFactory.get_equipment_by_name("Shield")
    f.equip_item(eq)
    eq = CombatEquipmentFactory.get_equipment_by_name("Helmet")
    f.equip_item(eq)

    f.print()
    f.take_damage(20)
    f.print()
    f.heal(30)
    f.print()
    CombatEquipment.dnd_dice_text_to_roll("1d3+1")
    CombatEquipment.dnd_dice_text_to_roll("1d6")
    CombatEquipment.dnd_dice_text_to_roll("2d3+1")

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

    @staticmethod
    def get_entity_by_name(name: str) -> Entity:
        e = None
        if name in EntityFactory.entities.index:
            row = EntityFactory.entities.loc[name]

            fg = text_to_color(row["FG"])
            bg = text_to_color(row["BG"])
            e = Entity(name=name,
                       description=row["Description"],
                       char=row["Char"],
                       fg=fg, bg=bg)

            e.add_properties(row.iloc[4:].to_dict())

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


class Inventory:
    def __init__(self):
        self.stackable_items = {}
        self.other_items = []

    def get_stackable_items(self)->dict:
        items={}
        for item_name, count in self.stackable_items.items():
            e = EntityFactory.get_entity_by_name(item_name)
            items[e] = count
        return items

    def get_other_items(self)->list:
        return list(self.other_items)


    def add_item(self, new_item: Entity)->bool:

        success = False

        # If the item is stackable then increase the number you are holding
        if new_item.get_property("IsStackable") == True:
            # If you don't have any of these set inventory count to 0
            if new_item.name not in self.stackable_items.keys() or self.stackable_items[new_item.name] == 0:
                self.stackable_items[new_item.name] = 0

            self.stackable_items[new_item.name] += 1
            success = True
        else:
            self.other_items.append(new_item)
            success = True

        return success

    def remove_item(self, old_item):

        success = False

        # If the item is stackable then decrease the number you are holding
        if old_item.get_property("IsStackable") == True:
            # If you don't have any of these set inventory count to 1
            if old_item.name not in self.stackable_items.keys() or self.stackable_items[old_item.name] == 0:
                self.stackable_items[old_item.name] = 1

            self.stackable_items[old_item.name] -= 1

            if self.stackable_items[old_item.name] == 0:
                del self.stackable_items[old_item.name]

            success = True
        else:
            self.other_items.remove(old_item)
            success = True

        return success

    