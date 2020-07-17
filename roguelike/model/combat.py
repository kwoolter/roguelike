import pandas as pd
from pathlib import Path


class CombatClass:
    def __init__(self, name : str):
        self.name = name
        self.properties = {}

    def __str__(self):
        text = f'Class {self.name}: properties:{self.properties}'
        return text

    def add_properties(self, new_properties: dict):
        self.properties.update(new_properties)

    def get_property(self, property_name : str):
        return self.properties.get(property_name) == True

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
            e.add_properties(row.iloc[1:].to_dict())

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
        return self.properties.get(property_name) == True


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

        return e

class Fighter():

    def __init__(self, combat_class: CombatClass):
        self.combat_class = combat_class
        self.equipment = {}

    def equip_item(self, new_item : CombatEquipment):
        self.equipment[new_item.slot] = new_item

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
