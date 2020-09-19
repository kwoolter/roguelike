import copy
import math
import operator

import numpy as np
import tcod as libtcod

from roguelike.model.combat import *
from roguelike.model.races import Race
from roguelike.model.spells import SpellBook, Spell


def text_to_color(color_text: str) -> libtcod.color.Color:
    ''':param:'''

    try:
        c = eval(f'libtcod.{color_text.lower()}')
        if isinstance(c, libtcod.color.Color) is False:
            print("We didn't end up with a colour!")
            c = None
    except AttributeError:
        #print(f"{color_text} is not a valid attribute")
        c = None

    return c


class Entity():
    """
    The Entity class is for holding information about ALL items in the game.

    Attributes:
        STATE_xxxx (str):

    """
    STATE_INERT = "inert"
    STATE_ALIVE = "alive"
    STATE_DEAD = "dead"

    def __init__(self,
                 name: str,
                 description: str,
                 char: str,
                 category: str,
                 x: int = 0, y: int = 0,
                 fg=libtcod.white, bg=None,
                 state=STATE_INERT):
        """
        Create an instance of an Entity.

        :param name:
        :param description:
        :param char: the character to be used when drawing this entity on a console
        :param x: current x position of the Entity.  Default is 0
        :param y: current y position of the Entity.  Default is 0
        :param fg: foreground colour to be used when drawing entities' char.  Default white.
        :param bg: background colour to be used when drawing entities' char.  Default None.
        :param state:
        """

        # Properties
        self.name = name
        self.description = description
        self.char = char
        self.category = category
        self._state = state
        self.x = x
        self.y = y
        self.fg = fg
        self.bg = bg

        self.properties = {}

        # Components
        self.fighter = None
        self.combat_equipment = None

    def __str__(self):
        return f"Name:{self.name}, char:'{self.char}', xyz: {self.x}/{self.y}/{self.z}, properties:{self.properties.keys()}"

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

    @property
    def z(self):
        return self.get_property("Zorder")

    def add_properties(self, new_properties: dict):
        self.properties.update(new_properties)
        if self.get_property("IsEnemy") is True:
            self._state = Entity.STATE_ALIVE

    def get_property(self, property_name: str):
        return self.properties.get(property_name)

    def set_property(self, property_name: str, new_value):
        self.properties.update({property_name: new_value})

    def move(self, dx: int, dy: int):
        self.x += dx
        self.y += dy

    def distance_to_target(self, other_entity) -> float:
        return math.sqrt((self.x - other_entity.x) ** 2 + (self.y - other_entity.y) ** 2)


class Player(Entity):
    """
    Player is a class that specialises the Entity class principally by adding an inventory.
    Items can be added or removed to the player's inventory

    Attributes:
        MAX_INVENTORY_ITEMS (int): What is the max allowable size of the player's inventory

    """
    MAX_INVENTORY_ITEMS = 20

    def __init__(self, name: str,
                 description: str,
                 category: str,
                 char: str,
                 fg,
                 x: int = 0, y: int = 0):
        """
        Create a new instance of a Player.

        :param name: the name of the new player
        :param x: their current x position. Defaults to 0
        :param y: their current y position Defaults to 0
        """

        # Initialise parent class
        super().__init__(name=name,
                         description=description,
                         category=category,
                         char=char,
                         fg=fg,
                         x=x, y=y)

        # Components
        # Give the player an inventory to store items in
        self.inventory = Inventory(max_items=Player.MAX_INVENTORY_ITEMS)

    @property
    def combat_class_name(self):
        return self.fighter.combat_class.name

    @property
    def combat_class(self):
        return self.fighter.combat_class

    def print(self):
        print(f'{self.name} at {self.xy}')

    def get_property(self, property_name: str):
        value = self.properties.get(property_name)
        if value is None:
            value = self.fighter.get_property(property_name)
        return value

    def add_entity(self, new_entity: Entity):

        # Properties
        self.name = new_entity.name
        self.description = new_entity.description
        self.char = new_entity.char
        self.category = new_entity.category
        self._state = new_entity.state
        self.x = new_entity.x
        self.y = new_entity.y
        self.fg = new_entity.fg
        self.bg = new_entity.bg
        self.properties = copy.deepcopy(new_entity.properties)



    def heal(self, heal_amount: int):
        if self.fighter is not None:
            self.fighter.heal(heal_amount=heal_amount)

    def take_damage(self, damage_amount: int):
        if self.fighter is not None:
            self.fighter.take_damage(damage_amount)

    def equip_item(self, new_item: Entity, slot=None) -> bool:

        assert self.fighter is not None, "Trying to equip an item when you don't have a fighter set-up"

        # If new item is None then effectively we are just unequipping whatever is in the specified slot
        if new_item is None:
            success = self.fighter.equip_item(new_item, slot)

        # Check if the new item is equippable or is is something that you can collect and use e.g. a key
        elif new_item.get_property("IsEquippable") == True or \
                (new_item.get_property("IsCollectable") == True and new_item.get_property("IsInteractable") == True):

            # Equip the new item unequipping anything that was already equipped in that slot
            success = self.fighter.equip_item(new_item, slot)

        else:
            print(f"{new_item.name} is not equippable")
            success = False

        return success

    def take_item(self, new_item: Entity) -> bool:
        return self.inventory.add_item(new_item)

    def drop_item(self, old_item: Entity) -> bool:
        success = self.inventory.remove_item(old_item)
        self.fighter.unequip_item(old_item=old_item)
        return success

    def level_up(self):
        success = self.fighter.level_up()
        if success is True:
            self.heal(20)
        return success

    def get_stat_total(self, stat_name: str) -> int:
        """
        Get the total stat value for the specified stat name based on your equipment and combat class

        :param stat_name: the name of the stat that you want the total for
        :return: the total value that your equipment and combat class provides for the specified stat
        """

        # Get ALL of the stat totals from your equipment
        totals = self.fighter.get_equipment_stat_totals([stat_name])

        # Get the value of that your equipment provides
        total = totals.get(stat_name)
        if total is None:
            total = 0

        # Get thevalue of that stat that your combat class provides and add it to the total
        v = self.fighter.combat_class.get_property(stat_name)
        if v is not None:
            total += v

        return total


class Fighter():
    DEFAULT_WEAPON = None
    DEFAULT_WEAPON_NAME = "Hands"
    WEAPON_SLOT = "Main Hand"
    OFF_HAND = "Off Hand"
    ITEM_SLOT = "Item Slot"
    SPELL_SLOT = "spell Slot"

    DEFENSES = {"FORT":("STR", "CON"), "REF":("DEX","INT"), "WILL":("WIS","CHA")}

    def __init__(self, combat_class: CombatClass, race:Race = None):

        # Properties
        self.last_target = None
        self.combat_class = combat_class
        self.race = race
        self.set_property("Level", 0)
        self.set_property("HP", self.get_max_HP())
        self.is_under_attack = False

        # Components
        self.equipment = {}
        Fighter.DEFAULT_WEAPON = EntityFactory.get_entity_by_name(Fighter.DEFAULT_WEAPON_NAME)
        self.spell_book = SpellBook(self.combat_class.name)

        if race is not None:
            self.combat_class.add_properties(race.properties, increment=True)

    @property
    def is_dead(self) -> bool:
        return self.combat_class.get_property("HP") <= 0

    @property
    def level(self) -> int:
        return self.combat_class.get_property("Level")

    @property
    def current_weapon(self) -> Entity:
        eq = self.equipment.get(Fighter.WEAPON_SLOT)
        if eq is None:
            eq = Fighter.DEFAULT_WEAPON
        return eq

    @property
    def current_item(self) -> Entity:
        eq = self.equipment.get(Fighter.ITEM_SLOT)
        return eq

    @property
    def current_weapon_details(self) -> CombatEquipment:
        eq = self.equipment.get(Fighter.WEAPON_SLOT)

        # Forge a default attack for the Fighter if no weapon equipped
        if eq is None:
            # Get a basic weapon
            ce = CombatEquipmentFactory.get_equipment_by_name("Default Weapon")

            # Specialise it using default attack properties of this Combat Class
            ce.name = self.get_property("DefaultATK")
            ce.description = self.get_property("DefaultATK")
            ce.set_property("Range", self.get_property("DefaultATKRange"))
            ce.set_property("DMG", self.get_property("DefaultATKDice"))

        # Otherwise get the details of the equipped weapon
        else:
            ce = CombatEquipmentFactory.get_equipment_by_name(eq.name)

        return ce

    def get_property(self, property_name: str):
        property_value = self.combat_class.get_property(property_name)
        return property_value

    def set_property(self, property_name: str, new_value: int, increment: bool = False):
        self.combat_class.update_property(property_name, new_value, increment)

    def get_property_modifier(self, property_name: str):
        """

        :param property_name:
        :return:
        """
        modifier = 0
        property_value = self.combat_class.properties.get(property_name)
        if property_value is not None:
            modifier = math.floor((property_value - 10) / 2)
        return modifier

    def get_max_HP(self) -> int:

        # If this is a playable character then use their Constitution
        if self.combat_class.get_property("Playable") == True:
            con = self.get_property("CON")
        # Else not required as already baked into "Level1HP" stat
        else:
            con = 0

        level = self.get_property("Level")
        level_1_HP = self.get_property("Level1HP")
        HP_per_level = self.get_property("HPPerLevel")

        return con + level_1_HP + ((level - 1) * HP_per_level)

    def get_stat_total(self, stat_name: str) -> int:

        # Get the stat total from your equipment
        totals = self.get_equipment_stat_totals([stat_name])
        total = totals.get(stat_name)
        if total is None:
            total = 0

        # Get the same stat from your abilities and add it
        v = self.combat_class.get_property(stat_name)
        if v is not None:
            total += v

        # print(f'\tEquipment {stat_name} total = {total}')

        return total

    def get_attack(self, ability: str = "STR"):
        """
        Get the fighter's attack power for the specified ability.  Default = STR
        :param ability: the nme of the ability that you will be using to attack
        :return: current total attack power
        """
        ability_modifier = self.get_property_modifier(ability)
        attacker_level = self.get_property("Level")
        attack = ability_modifier + math.floor(attacker_level / 2)

        return attack

    def get_defence(self, defense: str = "AC"):
        """
        Get the fighter's defence that uses the specified ability
        :param defense: the nme of the ability that you will be using to attack
        :return: current total defence value
        """

        # Special calculation for AC defense
        if defense == "AC":
            # If this is a playable character then add bonus
            if self.combat_class.get_property("Playable") == True:
                bonus = 10 + self.level/2
            # Else not required as already part of AC stats for the fighter
            else:
                bonus = 0

            defense = self.get_stat_total(defense) + bonus

        # Standard calculation for other defenses
        else:
            class_bonus = self.get_property(defense)
            ability1, ability2 = Fighter.DEFENSES[defense]
            modifier = max(self.get_property_modifier(ability1), self.get_property_modifier(ability2))
            defense = modifier + 10 + self.level/2 + class_bonus

        return int(defense)

    def take_damage(self, damage_amount: int):
        self.combat_class.update_property("HP", damage_amount * -1, increment=True)

    def heal(self, heal_amount: int):
        new_hp = min(self.combat_class.get_property("HP") + heal_amount, self.get_max_HP())
        self.combat_class.update_property("HP", new_hp)

    def add_XP(self, xp_amount: int):
        self.combat_class.update_property("XP", xp_amount, increment=True)

    def add_kills(self, kill_count: int = 1):
        self.combat_class.update_property("KILLS", kill_count, increment=True)

    def level_up(self)->bool:
        """
        Level up a Fighter
        """

        success = True

        level = self.get_property("Level")
        if level is None:
            level = 1
        else:
            level += 1

        self.set_property("Level", level)

        # Get the next level and add its new properties to ours
        new_level = LevelFactory.get_level_info(level)
        for k,v in new_level.properties.items():
            self.set_property(k,v,increment=True)

        # Recalculate our Max HP
        self.set_property("MaxHP", self.get_max_HP())

        # Update our spell book with the new level and allowed number of spells
        spell_caps = {frequency:self.get_property(frequency) for frequency in Spell.FREQUENCIES}
        self.spell_book.level_up(level, spell_caps)

        return success

    def ability_upgrade(self, ability_name=None):
        """
        Upgrade the specified ability and decrement the available Ability Points.
        :param ability_name: the name of the ability that you want to upgrade
        :return: True
        """
        self.combat_class.update_property(property_name=ability_name, new_value=1, increment=True)
        self.set_property("Ability Points", -1, increment=True)

        # Recalculate our Max HP
        self.set_property("MaxHP", self.get_max_HP())

        return True


    def equip_item(self, new_item: Entity, slot: str = None) -> bool:
        """
        Equip an item in the specified equipment slot.
        :param new_item: the new item that we are equipping.  If None you are un-eqipping back to inventory
        :param slot: which slot we want to equip it to.  Default None which uses the combat equipment slot
        :return: the item that was replaced in the equipment slot
        """

        success = True

        # If no new item is being equipped then remove existing item from the slot
        if new_item is None:
            if slot is not None and slot in self.equipment:
                del self.equipment[slot]
        else:

            # Get the CombatClass details of the new item
            new_eq = CombatEquipmentFactory.get_equipment_by_name(new_item.name)

            # If no slot specified use the default slot for this type of equipment
            if slot is None:
                slot = new_eq.slot

            # If trying to equip in off hand slot...
            if slot == Fighter.OFF_HAND:

                # Check if you are already using a 2 handed weapon and fail if you are!
                main_hand = self.equipment.get(Fighter.WEAPON_SLOT)
                if main_hand is not None:
                    main_eq = CombatEquipmentFactory.get_equipment_by_name(main_hand.name)
                    if main_eq.get_property("HANDS") == "2H":
                        print(f'Can not equip offhand slot with 2H weapon {main_hand.name}')
                        success = False

            # Else If trying to equip a 2H weapon in main hand then unequip off hand item
            elif slot == Fighter.WEAPON_SLOT and new_eq.get_property("HANDS") == "2H":
                self.equip_item(None, Fighter.OFF_HAND)

            # If good to go then equip slot with the new item
            if success is True:
                self.equipment[slot] = new_item

        return success

    def unequip_item(self, old_item: Entity):

        del_keys = []
        for k, v in self.equipment.items():
            if v == old_item:
                del_keys.append(k)

        for k in del_keys:
            del self.equipment[k]

        return len(del_keys) > 0

    def is_equipped(self, item: Entity):
        return item in self.equipment.values()

    def get_equipment_stat_totals(self, stat_names: list = ["AC", "INT", "Weight", "Value"]):
        """

        :param stat_names:
        :return:
        """
        totals = {}

        for stat in stat_names:
            totals[stat] = 0
            for e in self.equipment.values():
                eq = CombatEquipmentFactory.get_equipment_by_name(e.name)
                if eq is not None:
                    v = eq.get_property(stat)
                    if v is not None:
                        totals[stat] += v

        return totals

    def learn_spell(self, new_spell:Spell):
        self.spell_book.learn_spell(new_spell)

    def memorise_spell(self, new_spell:Spell):
        return self.spell_book.memorise_spell(new_spell)

    def roll_damage(self) -> int:
        dmg = CombatEquipmentFactory.get_damage_roll_by_name(self.current_weapon.name)
        return dmg

    def roll_ability_check(self, ability:str, difficulty:str="Medium")->bool:

        success_levels = {"Very easy":5,
                          "Easy":10,
                          "Medium":15,
                          "Hard":20,
                          "Very hard":25,
                          "Nearly impossible":30}

        difficulty_value = success_levels[difficulty]
        ability_modifier = self.get_property_modifier(ability)

        return random.randint(1,20) + ability_modifier >= difficulty_value



    def get_XP_reward(self) -> int:
        """
        Calculate and return the XP reward for defeating this Fighter
        :return: the XP reward
        """

        reward = self.get_property("XP")
        if reward is None:
            reward = 0

        return reward

    def print(self):
        print(f'Fighter ({self.combat_class.name})')
        for k, v in self.combat_class.properties.items():
            print(f'\t{k}={v}')
        print("Equipment:")
        for k, v in self.equipment.items():
            print(f'\t{k}={str(v)}')


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
        df = EntityFactory.entities
        df.set_index("Name", drop=True, inplace=True)
        df["IsTradable"] = EntityFactory.entities["Value"] > 0

        print(df.head())
        print(df.dtypes)

        # self.entities.set_index(self.entities.columns[0], drop=True, inplace=True)

    @staticmethod
    def get_entity_by_name(name: str) -> Entity:

        assert EntityFactory.entities is not None, "No entities have been loaded!"

        e = None
        if name in list(EntityFactory.entities.index):
            row = EntityFactory.entities.loc[name]

            e = EntityFactory.entity_from_row(name, row)

        else:
            print(f"Can't find entity {name} in factory!")

        return e

    @staticmethod
    def get_entities_by_property(property_name: str, property_value: bool = True) -> list:

        matches = []
        df = EntityFactory.entities

        if property_name in df.columns:

            q = f'{property_name} == {property_value}'
            matched = df.query(q)

            for index, row in matched.iterrows():
                e = EntityFactory.entity_from_row(index, row)
                matches.append(e)
        else:
            print(f"Can't find property {property_name} in factory!")

        return matches

    @staticmethod
    def get_entities_by_category(category_name: str) -> list:

        matches = []
        df = EntityFactory.entities

        q = f"Category == '{category_name}'"
        matched = df.query(q)

        for index, row in matched.iterrows():
            e = EntityFactory.entity_from_row(index, row)

            matches.append(e)

        return matches

    @staticmethod
    def entity_from_row(index, row) -> Entity:

        name = index
        fg = text_to_color(row["FG"])
        bg = text_to_color(row["BG"])
        e = Entity(name=name,
                   description=row["Description"],
                   char=row["Char"],
                   category=row["Category"],
                   fg=fg,
                   bg=bg)

        e.add_properties(row.iloc[5:].to_dict())

        return e


class Level():
    def __init__(self, level_id: int, xp: int):
        self.level_id = level_id
        self.xp = xp
        self.properties = {}

    def add_properties(self, new_properties: dict):
        self.properties.update(new_properties)

    def __str__(self):
        return f'Level {self.level_id}: XP({self.xp})'

class LevelFactory:

    levels = None
    level_id_to_level = {}



    def __init__(self):
        pass

    @staticmethod
    def load(file_name:str):

        # Create path for the file that we are going to load
        data_folder = Path(__file__).resolve().parent
        file_to_open = data_folder / "data" / file_name

        # Read in the csv file
        LevelFactory.levels = pd.read_csv(file_to_open)
        df = LevelFactory.levels
        df.set_index("Level", drop=True, inplace=True)

    @staticmethod
    def row_to_level(level_id:int, row)->Level:

        xp = row["XP"]
        new_level = Level(level_id=level_id, xp=xp)
        new_level.add_properties(row.iloc[1:].to_dict())

        return new_level

    @staticmethod
    def get_level_info(level_id:int):
        df = LevelFactory.levels
        row = df.loc[(level_id)]
        level = LevelFactory.row_to_level(level_id, row)
        return level

    @staticmethod
    def xp_to_level(xp:int)->Level:
        df = LevelFactory.levels
        i =  df.loc[df.XP <= xp,['XP']].idxmax()[0]

        return LevelFactory.row_to_level(i, df.loc[(i)])

    @staticmethod
    def xp_to_next_level(xp:int)->int:
        df = LevelFactory.levels
        i = df.loc[df.XP > xp,['XP']].min()
        return i['XP']


class Inventory:
    GOLD = "Gold"
    SILVER = "Silver"
    COPPER = "Copper"
    COINS = {GOLD:100, SILVER:10, COPPER:1}

    def __init__(self, max_items: int = 15):
        self.max_items = max_items
        self.stackable_items = {}
        self.other_items = []
        self.coins = {c_name: 0 for c_name in Inventory.COINS}
        self.money = 0

    @property
    def items(self) -> int:
        return len(self.other_items) + len(self.stackable_items)

    @property
    def full(self):
        return self.items >= self.max_items

    def is_held(self, item : Entity)->bool:
        success = False

        if item in self.other_items:
            success = True
        elif item.name in self.stackable_items:
            success = True

        return success


    def get_stackable_items(self) -> dict:
        items = {}
        for item_name, count in self.stackable_items.items():
            e = EntityFactory.get_entity_by_name(item_name)
            items[e] = count
        return items

    def get_other_items(self) -> list:
        return list(self.other_items)

    def get_money(self)->int:
        return self.money

    def get_coins(self)->dict:
        return Inventory.value_to_gsb_coin_text(self.money)

    def buy_item(self, new_item: Entity)->bool:
        success = False

        cost = new_item.get_property("Value")

        # Have we got enough money to buy the item?
        if self.money >= cost:
            success = self.add_item(new_item)
            if success is True:
                self.money -= cost

        return success

    def sell_item(self, old_item : Entity)-> bool:

        success = False

        if self.is_held(old_item) is True:

            if self.remove_item(old_item) is True:

                cost = old_item.get_property("Value")
                self.money += cost
                success = True

        return success

    def add_item(self, new_item: Entity) -> bool:

        success = False

        # If the new item is a coin then add value to our money
        if new_item.name in self.coins:
            value = Inventory.COINS[new_item.name]
            self.money += value
            success = True

        # Have we got room in the inventory?
        elif self.full is False or (
                new_item.get_property("IsStackable") == True and new_item.name in self.stackable_items.keys()):

            # If the item is stackable then increase the number you are holding
            if new_item.get_property("IsStackable") == True:
                # If you don't have any of these set inventory count to 0
                if new_item.name not in self.stackable_items.keys() or self.stackable_items[new_item.name] == 0:
                    self.stackable_items[new_item.name] = 0

                self.stackable_items[new_item.name] += 1
                success = True
            else:
                self.other_items.append(new_item)
                self.other_items.sort(key=operator.attrgetter('description'))
                success = True

        return success

    def remove_item(self, old_item):

        success = False

        # If the old item is a coin then remove from our total money
        if old_item.name in self.coins:
            value = old_item.get_property("Value")
            self.money -= value
            success = True

        else:

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
                if old_item in self.other_items:
                    self.other_items.remove(old_item)
                success = True

        return success

    @staticmethod
    def gsb_coin_text_to_value(coin_text:str):

        result = 0

        # Define regex for parsing the text
        gold = re.compile(r'^\d+(?=g)')
        silver = re.compile(r'\d+(?=s)')
        bronze = re.compile(r'\d+(?=b)')

        # Use regex to extract the dice info from the text
        gs = gold.search(coin_text)
        ss = silver.search(coin_text)
        bs= bronze.search(coin_text)

        g = 0 if gs is None else int(gs[0])
        s = 0 if ss is None else int(ss[0])
        b = 0 if bs is None else int(bs[0])

        result = (g * Inventory.COINS[Inventory.GOLD]) + \
                 (s * Inventory.COINS[Inventory.SILVER]) + \
                 (b * Inventory.COINS[Inventory.COPPER])

        print(f'g{g}:s{s}:b{b}={result}')

        return result


    @staticmethod
    def value_to_gsb_coin_text(value : int)->dict:

        coins_by_value = np.array(sorted(Inventory.COINS.items(), key=lambda x: x[1], reverse = True))

        coins = {c:0 for c in Inventory.COINS.keys()}

        for c in coins_by_value[:,0]:
            v = Inventory.COINS[c]
            coin_count = value // v
            coins[c] = coin_count
            value -= coin_count * v

        return coins


if __name__ == "__main__":

    LevelFactory.load("levels.csv")

    l = LevelFactory.get_level_info(1)
    print(str(l))

    xps = [1000,5000,6000,7000,20000]
    for xp in xps:
        l = LevelFactory.xp_to_level(xp)
        xp_to_next = LevelFactory.xp_to_next_level(xp)

        print(f'xp={xp} -> Level={l.level_id}, level up at {xp_to_next}')

    assert False

    text = "1g2s3b"
    r = Inventory.gsb_coin_text_to_value(text)
    print(f'{text}={r}')

    text = "3b"
    r = Inventory.gsb_coin_text_to_value(text)
    print(f'{text}={r}')

    text = "2s"
    r = Inventory.gsb_coin_text_to_value(text)
    print(f'{text}={r}')

    v = 15
    r = Inventory.value_to_gsb_coin_text(v)
    print(f'{v}={r}')

    assert False


    EntityFactory.load("entities.csv")

    entities = []

    names = {"Player", "Corpse", "Stairs Up", "Orc", "Dagger"}

    for name in names:
        for c in range(random.randint(1, 3)):
            new_enity = EntityFactory.get_entity_by_name(name)
            entities.append(new_enity)

    print(entities)

    e = EntityFactory.get_entity_by_name("rubbish")
    e = EntityFactory.get_entity_by_name("Gold")
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

    matches = EntityFactory.get_entities_by_property("IsEnemy")
    print(matches)
