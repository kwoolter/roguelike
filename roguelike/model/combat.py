import pandas as pd
from pathlib import Path
import re
import random


class CombatClass:

    def __init__(self, name : str):
        self.name = name
        self.properties = {"KILLS":0, "XP":0}

    def __str__(self):
        text = f'Class {self.name}: properties:{self.properties}'
        return text

    def add_properties(self, new_properties: dict):
        self.properties.update(new_properties)

    def get_property(self, property_name : str):
        return self.properties.get(property_name)

    def update_property(self, property_name : str, new_value : float, increment=False):
        if property_name in self.properties.keys():
            if increment is False:
                self.properties[property_name] = new_value
            else:
                self.properties[property_name] += new_value
        else:
            print(f"Can't find property {property_name} in {self.name} list of properties")



class CombatClassFactory:
    combat_classes = None

    def __init__(self):
        pass

    @staticmethod
    def load(file_name: str):

        # Create path for the file that we are going to load
        data_folder = Path(__file__).resolve().parent
        file_to_open = data_folder / "data" / file_name

        # Read in the csv file
        CombatClassFactory.combat_classes = pd.read_csv(file_to_open)
        CombatClassFactory.combat_classes.set_index("Name", drop=True, inplace=True)

    @staticmethod
    def get_combat_class_by_name(name: str) -> CombatClass:
        e = None
        if name in CombatClassFactory.combat_classes.index:
            row = CombatClassFactory.combat_classes.loc[name]
            e = CombatClass(name)
            e.add_properties(row.iloc[:].to_dict())

        else:
            print(f"Can't find combat class {name} in factory!")

        return e

class CombatEquipment:
    def __init__(self, name : str, description : str, slot :str):
        self.name = name
        self.description = description
        self.slot = slot
        self.properties = {}

    def __str__(self):
        text = f'Equipment: {self.name} ({self.description}): slot:{self.slot} properties:{self.properties}'
        return text

    def add_properties(self, new_properties: dict):
        self.properties.update(new_properties)

    def get_property(self, property_name : str):
        return self.properties.get(property_name)

    def get_damage_roll(self)->int:
        dmg_dice = self.get_property("DMG")
        return CombatEquipment.dnd_dice_text_to_roll(dmg_dice)



    @staticmethod
    def dnd_dice_text_to_roll(dice_text:str):

        number_of_dice = re.compile(r'^\d+(?=d)')
        dice_sides = re.compile(r'(?<=\dd)\d+')
        extra_bonus = re.compile(r'(?<=\d\+)\d+$')

        r = number_of_dice.search(dice_text)
        assert r is not None, "Can't find number of dice"
        num_dice = int(r[0])
        r = dice_sides.search(dice_text)
        assert r is not None, "Can't find number of dice sides"
        num_dice_sides = int(r[0])
        r = extra_bonus.search(dice_text)
        if r is not None:
            bonus = int(r[0])
        else:
            bonus = 0

        result = 0

        for i in range(num_dice):
            result += random.randint(1,num_dice_sides)
        result += bonus

        print(f"Rolling {num_dice} x {num_dice_sides} sided dice + {bonus} = {result}")

        return result


class CombatEquipmentFactory:
    combat_equipment = None

    def __init__(self):
        pass

    @staticmethod
    def load(file_name: str):

        # Create path for the file that we are going to load
        data_folder = Path(__file__).resolve().parent
        file_to_open = data_folder / "data" / file_name

        # Read in the csv file
        CombatEquipmentFactory.combat_equipment = pd.read_csv(file_to_open)
        CombatEquipmentFactory.combat_equipment.set_index("Name", drop=True, inplace=True)

    @staticmethod
    def get_equipment_by_name(name: str) -> CombatEquipment:
        e = None
        if name in CombatEquipmentFactory.combat_equipment.index:
            row = CombatEquipmentFactory.combat_equipment.loc[name]
            e = CombatEquipment(name=name, description=row["Description"], slot = row["Slot"])
            e.add_properties(row.iloc[2:].to_dict())

        else:
            print(f"Can't find combat equipment {name} in factory!")
            print(f'Index: {CombatEquipmentFactory.combat_equipment.index}')

        return e

    @staticmethod
    def get_damage_roll_by_name(equipment_name: str):
        eq = CombatEquipmentFactory.get_equipment_by_name(equipment_name)
        if eq is not None:
            dmg = eq.get_damage_roll()
        else:
            print(f"{__class__}: Can't ding equipment {equipment_name}")
            dmg = 0

        return dmg


