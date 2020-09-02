import pandas as pd
from pathlib import Path
import roguelike.model.combat as combat

class Spell:
    def __init__(self, name: str,
                 description:str,
                 attack_ability: str,
                 defence: str,
                 damage:str,
                 range:int):

        self.name = name
        self.description = description
        self.attack_ability = attack_ability
        self.defense = defence
        self.damage = damage
        self.range = range

    def roll_damage(self) -> int:
        dmg = combat.CombatEquipment.dnd_dice_text_to_roll(self.damage)
        return dmg

    def __str__(self):
        return f'{self.name}:{self.description} ATK({self.attack_ability}) vs DEF({self.defense})'

class SpellBook:
    def __init__(self):
        self.learned_spells = set()
        self.memorised_spells = set()
        self.max_learned_spells = 3
        self.max_memorised_spells = 10

    def add_spell(self, new_spell:Spell)->bool:
        success = False

        if len(self.learned_spells) < self.max_learned_spells:
            self.learned_spells.add(new_spell)
            success = True

        return success

    def memorise_spell(self, new_spell):
        success = False

        if len(self.memorised_spells) < self.max_memorised_spells:
            self.memorised_spells.add(new_spell)
            success = True

        return success

    def print(self):
        for spell in self.learned_spells:
            print(str(spell))

class SpellFactory:
    spells = None

    def __init__(self):
        pass

    @staticmethod
    def load(file_name: str):
        # Create path for the file that we are going to load
        data_folder = Path(__file__).resolve().parent
        file_to_open = data_folder / "data" / file_name

        # Read in the csv file
        SpellFactory.spells = pd.read_csv(file_to_open)
        df = SpellFactory.spells
        df.set_index(["Class","Name"], drop=True, inplace=True)

        print(df.head())
        print(df.dtypes)


    @staticmethod
    def row_to_spell(row)->Spell:


        name = row.index
        description = row["Description"]
        atk = row["ATK"]
        defence = row["DEF"]
        dmg = row["DMG"]
        range = row["Range"]
        level = row["Level"]
        freq = row["Frequency"]

        new_spell = Spell(name=name,
                          description=description,
                          attack_ability=atk,
                          defence = defence,
                          damage=dmg,
                          range=range)

        return new_spell


    @staticmethod
    def get_spells_by_class(class_name:str, level:int = None):

        spell_list = []

        df = SpellFactory.spells

        r = df.loc[(class_name)]

        for i, row in r.iterrows():
            new_spell = SpellFactory.row_to_spell(row)
            spell_list.append(new_spell)


        return spell_list


if __name__ == "__main__":
    SpellFactory.load("spells.csv")

    my_book = SpellBook()

    r = SpellFactory.get_spells_by_class("Wizard")

    for rr in r:
        my_book.add_spell(rr)


    my_book.print()

