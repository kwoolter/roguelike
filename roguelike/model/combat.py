import pandas as pd
from pathlib import Path
import re
import random
import logging

def dnd_dice_text_to_roll(dice_text: str):
    """

    :param dice_text: the DnD text representation of dice
    :return: the result of rolling the dice combo
    """
    # Define regex for parsing the text
    number_of_dice = re.compile(r'^\d+(?=d)')
    dice_sides = re.compile(r'(?<=\dd)\d+')
    extra_bonus = re.compile(r'(?<=\d\+)\d+$')

    # Use regex to extract the dice info from the text
    r = number_of_dice.search(dice_text)
    assert r is not None, "Can't find number of dice"
    num_dice = int(r[0])
    r = dice_sides.search(dice_text)
    assert r is not None, "Can't find number of dice sides"
    num_dice_sides = int(r[0])

    # Bonus is optional
    r = extra_bonus.search(dice_text)
    if r is not None:
        bonus = int(r[0])
    else:
        bonus = 0

    # Now time to roll the dice!
    result = 0

    for i in range(num_dice):
        result += random.randint(1, num_dice_sides)
    result += bonus

    print(f"Rolling {num_dice} x {num_dice_sides} sided dice + {bonus} = {result}")

    return result


class CombatClass:

    def __init__(self, name : str):
        self.name = name
        self.properties = {"KILLS":0, "XP":0}

    def __str__(self):
        text = f'Class {self.name}: properties:{self.properties}'
        return text

    def add_properties(self, new_properties: dict):
        self.properties.update(new_properties)
        self.properties["HP"] = self.properties["Level1HP"]

    def get_property(self, property_name : str):
        return self.properties.get(property_name)

    def update_property(self, property_name : str, new_value : float, increment=False):
        if increment is False or property_name not in self.properties:
            self.properties[property_name] = new_value
        else:
            self.properties[property_name] += new_value

class CombatClassFactory:
    combat_classes = None
    STANDARD_ABILITIES = ["STR", "CON", "INT", "DEX", "CHA", "WIS"]
    STANDARD_ARRAY = [16, 14, 13, 12, 11, 10]

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

        print(CombatClassFactory.combat_classes.tail(10))

    @staticmethod
    def get_combat_class_by_name(name: str) -> CombatClass:
        ccf = CombatClassFactory.combat_classes
        e = None
        if name in list(ccf.index):
            row = ccf.loc[name]
            e = CombatClass(name)
            e.add_properties(row.iloc[:].to_dict())

            if e.get_property("Level1HP") <= 0:
                hp_dice = e.get_property("Level1HPDice")
                hp = dnd_dice_text_to_roll(hp_dice)
                e.update_property("Level1HP", hp)

                print(f'{e.name}: rolled HP {hp_dice}={hp}')


        else:
            logging.warning(f"Can't find combat class {name} in factory!")

        return e

    @staticmethod
    def get_playable_classes(playable:bool = True)->list:
        ccf = CombatClassFactory.combat_classes
        rows = ccf[ccf.Playable == playable]
        return list(rows.index)

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

    def set_property(self, property_name: str, new_value:int):
        self.properties[property_name] = new_value

    def get_damage_roll(self)->int:
        dmg_dice = self.get_property("DMG")
        return dnd_dice_text_to_roll(dmg_dice)


    @staticmethod
    def dnd_dice_text_to_roll(dice_text:str):
        """

        :param dice_text: the DnD text representation of dice
        :return: the result of rolling the dice combo
        """
        # Define regex for parsing the text
        number_of_dice = re.compile(r'^\d+(?=d)')
        dice_sides = re.compile(r'(?<=\dd)\d+')
        extra_bonus = re.compile(r'(?<=\d\+)\d+$')

        # Use regex to extract the dice info from the text
        r = number_of_dice.search(dice_text)
        assert r is not None, "Can't find number of dice"
        num_dice = int(r[0])
        r = dice_sides.search(dice_text)
        assert r is not None, "Can't find number of dice sides"
        num_dice_sides = int(r[0])

        # Bonus is optional
        r = extra_bonus.search(dice_text)
        if r is not None:
            bonus = int(r[0])
        else:
            bonus = 0

        # Now time to roll the dice!
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
            logging.info(f"Can't find combat equipment {name} in factory!")

        return e

    @staticmethod
    def get_damage_roll_by_name(equipment_name: str):
        eq = CombatEquipmentFactory.get_equipment_by_name(equipment_name)
        if eq is not None:
            dmg = eq.get_damage_roll()
        else:
            print(f"{__class__}: Can't find equipment {equipment_name}")
            dmg = 0

        return dmg


if __name__ == "__main__":



    CombatClassFactory.load("combat_classes.csv")


    r = CombatClassFactory.get_combat_class_by_name("Fighter")
    print(r)

    r = CombatClassFactory.get_combat_class_by_name("Standard")
    print(r)


    r = CombatClassFactory.get_playable_classes()
    print(r)

    r = CombatClassFactory.get_playable_classes(playable=False)
    print(r)

