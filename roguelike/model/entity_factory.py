import math
import random

import tcod as libtcod

from .combat import CombatClass, CombatEquipmentFactory, CombatEquipment


def text_to_color(color_text: str) -> libtcod.color.Color:
    ''':param:'''

    try:
        c = eval(f'libtcod.{color_text.lower()}')
        if isinstance(c, libtcod.color.Color) is False:
            print("We didn't end up with a colour!")
            c = None
    except AttributeError:
        # print(f"{color_text} is not a valid attribute")
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
    def combat_class(self):
        return self.fighter.combat_class.name

    def get_property(self, property_name: str):
        value = self.properties.get(property_name)
        if value is None:
            value = self.fighter.get_property(property_name)
        return value

    def heal(self, heal_amount: int):
        if self.fighter is not None:
            self.fighter.heal(heal_amount=heal_amount)

    def equip_item(self, new_item: Entity, slot=None) -> bool:

        assert self.fighter is not None, "Trying to equip an item when you don't have a fighter set-up"

        success = False

        if new_item is None:
            old_item = self.fighter.equip_item(new_item, slot)
            success = True

        elif new_item.get_property("IsEquippable") == True or \
                (new_item.get_property("IsCollectable") == True and new_item.get_property("IsInteractable") == True):

            old_item = self.fighter.equip_item(new_item, slot)
            # self.inventory.remove_item(new_item)

            # if old_item is not None:
            #     success = self.inventory.add_item(old_item)

            success = True

        else:
            print(f"{new_item.name} is not equippable")

        return success

    def take_item(self, new_item: Entity) -> bool:
        return self.inventory.add_item(new_item)

    def drop_item(self, old_item: Entity) -> bool:
        success = self.inventory.remove_item(old_item)
        self.fighter.unequip_item(old_item=old_item)
        return success

    def level_up(self, stat_name: str = None):
        success = self.fighter.level_up(stat_name)
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
    ITEM_SLOT = "Item Slot"

    def __init__(self, combat_class: CombatClass):
        self.last_target = None
        self.combat_class = combat_class
        self.equipment = {}
        Fighter.DEFAULT_WEAPON = EntityFactory.get_entity_by_name(Fighter.DEFAULT_WEAPON_NAME)
        self.set_property("Level", 0)
        self.set_property("HP", self.get_max_HP())

    @property
    def is_dead(self) -> bool:
        return self.combat_class.get_property("HP") < 0

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

        if eq is None:
            ce = CombatEquipmentFactory.get_equipment_by_name("Default Weapon")
            ce.name = self.get_property("DefaultATK")
            ce.description = self.get_property("DefaultATK")
            ce.set_property("DMG", self.get_property("DefaultATKDice"))

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

        # Get the same stat from your abilities add add it
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

    def get_defence(self, ability: str = "AC"):
        """
        Get the fighter's defence that uses the specified ability
        :param ability: the nme of the ability that you will be using to attack
        :return: current total defence value
        """

        # If this is a playable character then add bonus
        if self.combat_class.get_property("Playable") == True:
            bonus = 10
        # Else not required as already part of AC stats for the fighter
        else:
            bonus = 0

        defence = self.get_stat_total(ability)
        level = self.get_property("Level")
        return bonus + defence + math.floor(level / 2)

    def take_damage(self, damage_amount: int):
        self.combat_class.update_property("HP", damage_amount * -1, increment=True)

    def heal(self, heal_amount: int):
        new_hp = min(self.combat_class.get_property("HP") + heal_amount, self.get_max_HP())
        self.combat_class.update_property("HP", new_hp)

    def add_XP(self, xp_amount: int):
        self.combat_class.update_property("XP", xp_amount, increment=True)

    def add_kills(self, kill_count: int = 1):
        self.combat_class.update_property("KILLS", kill_count, increment=True)

    def level_up(self, stat_name=None):
        """
        Level up a Fighter and increase the specified stat.
        :param stat_name: the stat that you want to increase. Default is None.
        """

        success = True

        level = self.get_property("Level")
        if level is None:
            level = 1
        else:
            level += 1

        self.set_property("Level", level)

        if stat_name is not None:
            value = self.combat_class.get_property(stat_name)
            if value is None:
                value = 1
            else:
                value += 1

            self.combat_class.update_property(property_name=stat_name, new_value=value)

        self.set_property("MaxHP", self.get_max_HP())

        return success

    def equip_item(self, new_item: Entity, slot: str = None) -> Entity:
        """
        Equip an item in the specified equipment slot.
        :param new_item: the new item that we are equipping.  If None you are un-eqipping back to inventory
        :param slot: which slot we want to equip it to.  Default None which uses the combat equipment slot
        :return: the item that was replaced in the equipment slot
        """

        # If no slot specified use the default slot for this type of equipment
        if slot is None:
            new_eq = CombatEquipmentFactory.get_equipment_by_name(new_item.name)
            slot = new_eq.slot

        # Get any item that is currently equipped in the target slot
        existing_item = self.equipment.get(slot)

        # If no new item is being equipped then remove existing item from the slot
        if new_item is None:
            del self.equipment[slot]
        # Otherwise fill the slot with teh new item
        else:
            self.equipment[slot] = new_item

        return existing_item

    def unequip_item(self, old_item: Entity):

        del_keys = []
        for k, v in self.equipment.items():
            if v == old_item:
                del_keys.append(k)

        for k in del_keys:
            del self.equipment[k]

        return len(del_keys) > 0

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

    def roll_damage(self) -> int:
        dmg = CombatEquipmentFactory.get_damage_roll_by_name(self.current_weapon.name)
        return dmg

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
        EntityFactory.entities.set_index("Name", drop=True, inplace=True)
        EntityFactory.entities["IsTradable"] = EntityFactory.entities["Value"] > 0
        # self.entities.set_index(self.entities.columns[0], drop=True, inplace=True)

    @staticmethod
    def get_entity_by_name(name: str) -> Entity:
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

        e.add_properties(row.iloc[4:].to_dict())

        return e


class Inventory:
    GOLD = "Gold"
    SILVER = "Silver"
    BRONZE = "Bronze"
    COINS = (GOLD, SILVER, BRONZE)

    def __init__(self, max_items: int = 15):
        self.max_items = max_items
        self.stackable_items = {}
        self.other_items = []
        self.coins = {c_name: 0 for c_name in Inventory.COINS}

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

    def buy_item(self, new_item: Entity)->bool:
        success = False

        cost = new_item.get_property("Value")

        coin = Inventory.GOLD

        if self.coins[coin] >= cost:
            success = self.add_item(new_item)
            if success is True:
                self.coins[coin] -= cost

        return success

    def sell_item(self, old_item : Entity)-> bool:

        success = False

        if self.is_held(old_item) is True:

            if self.remove_item(old_item) is True:

                cost = old_item.get_property("Value")
                coin = Inventory.GOLD
                self.coins[coin] += cost
                success = True

        return success

    def add_item(self, new_item: Entity) -> bool:

        success = False

        # If the new item is a coin then add to our coin collection
        if new_item.name in self.coins:
            self.coins[new_item.name] += 1
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
                success = True

        return success

    def remove_item(self, old_item):

        success = False

        # If the old item is a coin then add to our coin collection
        if old_item.name in self.coins:
            self.coins[old_item.name] -= 1
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


if __name__ == "__main__":
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
