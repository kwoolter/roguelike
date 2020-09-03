import pandas as pd
from pathlib import Path
import roguelike.model.combat as combat

class SpellBookException(Exception):

    def __init__(self):
        super().__init__()

class Spell:
    def __init__(self,
                 class_name:str,
                 name: str,
                 description:str,
                 attack_ability: str,
                 defence: str,
                 damage:str,
                 range:int):

        self.class_name = class_name
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
    def __init__(self, class_name:str):
        self.class_name = class_name
        self.learned_spells = set()
        self.memorised_spells = set()
        self.max_learned_spells = 10
        self.max_memorised_spells = 3

    def learn_spell(self, new_spell:Spell)->bool:
        success = False


        if new_spell.class_name != self.class_name:
            raise SpellBookException(f"You are a {self.class_name}, you cannot learn {new_spell.class_name} spells")
        elif len(self.learned_spells) >= self.max_learned_spells:
            raise SpellBookException(f"No more free spell pages in your book - max {self.max_learned_spells}")
        else:
            self.learned_spells.add(new_spell)
            success = True


        return success

    def memorise_spell(self, new_spell):
        success = False

        learned_spell_names = [spell.name for spell in self.learned_spells]
        if new_spell.name  not in learned_spell_names:
            raise SpellBookException(f"You have not learned spell {new_spell.name}")
        elif len(self.memorised_spells) > self.max_memorised_spells:
            raise SpellBookException(f"You can't memorise anymore spells - max { self.max_memorised_spells}")
        else:
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
    def get_available_class_names()->list:
        class_list = []

        if SpellFactory.spells is not None:
            class_list = list(SpellFactory.spells.index.levels[0])

        return class_list

    @staticmethod
    def get_available_spell_names()->list:
        spell_list = []

        if SpellFactory.spells is not None:
            spell_list = list(SpellFactory.spells.index.levels[1])

        return spell_list

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
    def row_to_spell(class_name:str, spell_name:str, row)->Spell:

        description = row["Description"]
        atk = row["ATK"]
        defence = row["DEF"]
        dmg = row["DMG"]
        range = row["Range"]
        level = row["Level"]
        freq = row["Frequency"]

        new_spell = Spell(class_name=class_name,
                          name=spell_name,
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

        assert class_name in df.index

        r = df.loc[(class_name)]

        for i, row in r.iterrows():
            new_spell = SpellFactory.row_to_spell(class_name, i, row)
            spell_list.append(new_spell)

        return spell_list

    @staticmethod
    def get_spell_by_name(spell_name:str)->Spell:

        if spell_name not in SpellFactory.get_available_spell_names():
            raise SpellBookException(f"Spell {spell_name} does not exist")

        row = SpellFactory.spells.xs(spell_name,level=1)

        new_spell = SpellFactory.row_to_spell(row.index, spell_name, row)

        return new_spell


import random
if __name__ == "__main__":
    SpellFactory.load("spells.csv")

    class_names = SpellFactory.get_available_class_names()

    for class_name in class_names:

        print(f'** {class_name} **')
        my_book = SpellBook(class_name)

        r = SpellFactory.get_spells_by_class(class_name)

        for i in range(10):
            new_spell = random.choice(r)
            try:
                success = my_book.learn_spell(new_spell)
                if success is False:
                    print(f"Failed to learn spell {new_spell.name}:{new_spell.description}")
            except SpellBookException as e:
                print(e)
        my_book.print()

        spells = SpellFactory.get_available_spell_names()

        spell = SpellFactory.get_spell_by_name(random.choice(spells))

        print(str(spell))

