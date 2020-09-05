import pandas as pd
from pathlib import Path
from roguelike.model.dice import DnD_Dice


class SpellBookException(Exception):

    def __init__(self, description : str):
        self.description = description
        super().__init__()

    def __str__(self):
        return self.description



class Spell:

    FREQUENCY_AT_WILL = "At Will"

    def __init__(self,
                 class_name:str,
                 name: str,
                 description:str,
                 attack_ability: str,
                 defence: str,
                 damage:str,
                 level:int,
                 range:int,
                 frequency:str):

        self.class_name = class_name
        self.name = name
        self.description = description
        self.attack_ability = attack_ability
        self.defense = defence
        self.damage = damage
        self.level = level
        self.range = range
        self.frequency = frequency

        self.used = False

    def roll_damage(self) -> int:

        if self.used is True:
            dmg = 0
        else:

            dmg = DnD_Dice.roll_dice_from_text(self.damage)

            if self.frequency != Spell.FREQUENCY_AT_WILL:
                self.used = True

        return dmg

    def reset(self):


        self.used = False

    def tick(self):
        pass

    def __str__(self):
        return f'{self.name}:{self.description} ATK({self.attack_ability}) vs DEF({self.defense}: DMG={self.damage})'

class SpellBook:
    """
    Class to represent tha spell book of a specified class
    """

    def __init__(self, class_name:str):
        """

        Args:
            class_name: name of the class that this book belongs to
        """

        # Properties
        self.class_name = class_name
        self.max_learned_spells = 10
        self.max_memorised_spells = 3

        # Components
        self.learned_spells = {}
        self.memorised_spells = {}

    def learn_spell(self, new_spell:Spell)->bool:
        """
        Attempt to learn a new spell
        Args:
            new_spell: the new Spell object that you want to learn

        Returns:

        """
        success = False

        if new_spell.class_name != self.class_name:
            raise SpellBookException(f"You are a {self.class_name}, you cannot learn {new_spell.class_name} spells")
        elif len(self.learned_spells) >= self.max_learned_spells:
            raise SpellBookException(f"No more free spell pages in your book - max {self.max_learned_spells}")
        else:
            self.learned_spells[new_spell.name]=new_spell
            success = True

        return success

    def memorise_spell(self, new_spell):
        success = False

        if new_spell.name  not in self.learned_spells:
            raise SpellBookException(f"You have not learned spell {new_spell.name}")
        elif len(self.memorised_spells) >= self.max_memorised_spells:
            raise SpellBookException(f"You can't memorise anymore spells - max { self.max_memorised_spells}")
        else:
            self.memorised_spells[new_spell.name]=new_spell
            success = True

        return success


    def get_learned_spells(self):
        return list(self.learned_spells.values())

    def get_learned_spell_names(self):
        return list(self.learned_spells.keys())

    def get_learned_spell(self,spell_name):
        return self.learned_spells.get(spell_name)

    def get_memorised_spells(self):
        return list(self.memorised_spells.values())

    def get_memorised_spell_names(self):
        return list(self.memorised_spells.keys())

    def get_memorised_spell(self,spell_name):
        return self.memorised_spells.get(spell_name)


    def print(self):
        print(f'** {self.class_name} Spell Book **')
        print(f'** Learned Spells **')
        for spell in self.learned_spells:
            print(str(spell))

        print(f'** Memorised Spells **')
        for spell in self.memorised_spells:
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
    def row_to_spell(row)->Spell:

        class_name = row["Class"]
        spell_name = row["Name"]
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
                          level=level,
                          range=range,
                          frequency=freq)

        return new_spell


    @staticmethod
    def get_spells_by_class(class_name:str, level:int = None):

        spell_list = []

        df = SpellFactory.spells

        assert class_name in df.index

        r = df.xs(class_name, level=0, drop_level=False)
        r.reset_index(inplace=True)

        for i, row in r.iterrows():
            new_spell = SpellFactory.row_to_spell(row)
            spell_list.append(new_spell)

        return spell_list

    @staticmethod
    def get_spell_by_name(spell_name:str)->Spell:

        if spell_name not in SpellFactory.get_available_spell_names():
            raise SpellBookException(f"Spell {spell_name} does not exist")

        row = SpellFactory.spells.xs(spell_name,level=1,drop_level=False)
        row.reset_index(inplace=True)

        new_spell = SpellFactory.row_to_spell(row.iloc[0])

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

                my_book.memorise_spell(new_spell)
            except SpellBookException as e:
                print(e)

        # mem_spell = random.choice(list(my_book.learned_spells.values()))
        # my_book.memorise_spell(mem_spell)

        my_book.print()

    print("*"*50)

    spells = SpellFactory.get_available_spell_names()
    spell = SpellFactory.get_spell_by_name(random.choice(spells))

    print(str(spell))
    r = spell.roll_damage()
    print(f'{spell.name} did {r} damage')
    r = spell.roll_damage()
    print(f'{spell.name} did {r} damage')


    print("*" * 50)

    try:

        my_book = SpellBook("Cleric")

        new_spell = SpellFactory.get_spells_by_class("Wizard")[0]
        my_book.learn_spell(new_spell)

    except SpellBookException as e:
        print(e)


