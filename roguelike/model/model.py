import collections
import random

import numpy as np
import pygame.rect as rect
import tcod as libtcod

from .entity_factory import Entity, Player, EntityFactory, Fighter
from .combat import *
from .events import Event

class EventQueue():
    def __init__(self):
        self.events = collections.deque()

    def add_event(self, new_event: Event):
        self.events.append(new_event)

    def pop_event(self):
        return self.events.pop()

    def size(self):
        return len(self.events)

    def print(self):
        for event in self.events:
            print(event)


class Tunnel:
    DIRECTION_V_H = "VH"
    DIRECTION_H_V = "HV"
    DIRECTIONS = (DIRECTION_V_H, DIRECTION_H_V)

    def __init__(self, start_pos, end_pos, direction=None, fg=libtcod.white, bg=libtcod.black):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.fg = fg
        self.bg = bg

        if direction is None:
            self.direction = random.choice(Tunnel.DIRECTIONS)
        else:
            self.direction = direction

    def print(self):
        print(f'Tunnel running from {self.start_pos} to {self.end_pos} using {self.direction}')

    def get_segments(self):
        segments = []

        start_x, start_y = self.start_pos
        end_x, end_y = self.end_pos

        hy = start_y if self.direction == Tunnel.DIRECTION_H_V else end_y
        vx = end_x if self.direction == Tunnel.DIRECTION_H_V else start_x

        for x in range(min(start_x, end_x), max(start_x, end_x) + 1):
            segments.append((x, hy))

        for y in range(min(start_y, end_y), max(start_y, end_y) + 1):
            segments.append((vx, y))

        return segments


class Room:
    def __init__(self, name: str, w, h, fg=libtcod.white, bg=libtcod.black):
        self.name = name
        self.width = w
        self.height = h
        self.fg = fg
        self.bg = bg
        self.rect = rect.Rect(0, 0, w, h)

    @property
    def x(self):
        return self.rect.x

    @property
    def y(self):
        return self.rect.y

    @property
    def center(self):
        return self.rect.center

    @property
    def centerx(self):
        return self.rect.centerx

    @property
    def centery(self):
        return self.rect.centery

    def is_touching(self, other_room):
        return self.rect.colliderect(other_room.rect.inflate(2, 2)) > 0

    def contains_point(self, point):
        x, y = point
        return self.rect.collidepoint(x, y) > 0

    def get_random_pos(self):
        """Return a random position within this room"""
        return (self.x + random.randint(0,self.width-1), self.y + random.randint(0,self.height-1))

    def print(self):
        print(f'Room {self.name} located at {self.rect}')


class Floor():
    def __init__(self, name: str, width: int = 50, height: int = 50, level: int = 0):

        # Properties of this floor
        self.name = name
        self.width = width
        self.height = height
        self.rect = rect.Rect(0, 0, width, height)
        self.level = level

        '''        
        'room_max_size': room_max_size,
        'room_min_size': room_min_size,
        'max_rooms': max_rooms,
        'max_monsters_per_room': max_monsters_per_room,
        'max_items_per_room': max_items_per_room,
        '''

        # Contents of the floor
        self.player = None
        self.first_room = None
        self.current_room = None
        self.last_room = None
        self.room_count = 15
        self.map_rooms = {}
        self.map_tunnels = []
        self.entities = []
        self.bots = []

        # Which parts of the floor are:-
        # - Walkable?
        # - Have already been explored?
        # - Are in the current FOV?
        self.walkable = None
        self.explored = None
        self.fov_map = None
        self.fov_radius = 6

        self.events = None


    def initialise(self, events: EventQueue):

        self.events = events

        self.map_rooms = {}
        self.map_tunnels = []
        self.walkable = None
        self.explored = None
        self.fov_map = None

        last_room = None
        self.first_room = None

        for i in range(self.room_count):

            # Create a new room of random size
            new_room = Room(f'Room{i}', random.randint(4, 8), random.randint(4, 8))

            # If we were able to add the room to the map...
            if self.add_map_room(new_room) is True:

                # if this is not the first room then...
                if last_room is not None:
                    # Add some random entities to the room
                    self.add_entities_to_room(new_room)

                    # Create a tunnel to the previous room
                    new_tunnel = Tunnel(last_room.center, new_room.center)
                    self.map_tunnels.append(new_tunnel)
                else:
                    self.first_room = new_room

                # Make the new room the last room
                last_room = new_room

        self.last_room = new_room

        self.add_entities_to_floor()

        self.build_floor_map()


    def print(self):
        print(f'Floor {self.name}: ({self.width},{self.height})')
        for room in self.map_rooms.values():
            room.print()

        for tunnel in self.map_tunnels:
            tunnel.print()

    def add_player(self, new_player: Player, first_room = True):

        if first_room is True:
            x, y = self.first_room.center
        else:
            x, y = self.last_room.center

        self.player = new_player
        self.player.xy = (x, y)
        self.move_player(0, 0)

        for bot in self.bots:
            bot.set_instructions(new_target=self.player)
            print(bot)

    def add_entities_to_room(self, room : Room):

        l = self.level

        entities = (("Gold", (1+ l//3)*5, 1), ("Spider",20,1), ("Orc", 20, 3), ("Troll", 25, 1))
        for ename, eprob, emax in entities:
            for count in range(emax):
                if random.randint(1,100) < eprob:
                    rx,ry = room.get_random_pos()
                    if self.get_entity_at_pos((rx,ry)) is None:
                        new_entity = EntityFactory.get_entity_by_name(ename)
                        new_entity.xy = rx,ry
                        self.entities.append(new_entity)
                        if new_entity.get_property("IsEnemy") == True:
                            self.generate_new_enemy(new_entity)
                            new_bot = AIBotTracker(new_entity, self)
                            self.bots.append(new_bot)

    def generate_new_enemy(self, new_entity : Entity):

        class_name = random.choice(("Minion", "Guard", "Chief"))
        equipment = random.choice(("Hands", "Dagger", "Spear"))

        cc = CombatClassFactory.get_combat_class_by_name(class_name)
        eq = EntityFactory.get_entity_by_name(equipment)

        new_fighter = Fighter(combat_class=cc)
        new_fighter.equip_item(eq)
        new_entity.fighter = new_fighter
        new_fighter.print()

    def add_entities_to_floor(self):

        # Add the player
        if self.player is not None:
            self.add_player(self.player)

        entities_to_add = [("NPC",3),
                           ("Sword",5),
                           ("Axe",5),
                           ("Shield", 5),
                           ("Helmet", 5),
                           ("Leather Boots", 15),
                           ("Leather Armour", 15),
                           ("Key",1),
                           ("Fire Scroll",2),
                           ("Healing Scroll",2),
                           ("Chest", 2),
                           ("Locked Chest", 2),]

        # Add different stuff to random rooms across the floor
        for ename, ecount in entities_to_add:

            # Get list of all rooms on this floor but exclude the first and last rooms
            available_rooms = list(self.map_rooms.values())
            available_rooms.remove(self.first_room)
            available_rooms.remove(self.last_room)
            if len(available_rooms) > 0:
                for i in range(random.randint(0,ecount)):

                    # pick a random room
                    room=random.choice(available_rooms)

                    # Pick a random position in the room
                    rx, ry = room.get_random_pos()

                    # If there is nothing already there...
                    if self.get_entity_at_pos((rx, ry)) is None:

                        # Add a new entity to the floor at this location
                        new_entity = EntityFactory.get_entity_by_name(ename)
                        if new_entity is None:
                            print(f"Couldn't create entity by name of {ename}")
                            continue

                        new_entity.xy = rx,ry

                        self.entities.append(new_entity)

                        # Don't use this room again
                        available_rooms.remove(room)

        # If we are not at the top level add stairs back up to the previous level in the centre of the first room
        if self.level > 1:
            ename = "Up Stairs"
            new_entity = EntityFactory.get_entity_by_name(ename)
            new_entity.xy = self.first_room.center
            e = self.get_entity_at_pos(self.last_room.center)
            # Replace anything that is already there!
            if e is not None:
                self.remove_entity(e)
            #self.entities.append(new_entity)

        # In the last room add some stairs to the next level down
        ename = "Down Stairs"
        new_entity = EntityFactory.get_entity_by_name(ename)
        new_entity.xy = self.last_room.center
        e = self.get_entity_at_pos(self.last_room.center)
        # Replace anything that is already there!
        if e is not None:
            self.remove_entity(e)
        self.entities.append(new_entity)

    def move_player(self, dx, dy):
        # If the destination is a valid path...
        if self.move_entity(self.player, dx, dy) is True:

            self.recompute_fov()

            # See if we found something?
            e = self.get_entity_at_pos(self.player.xy)
            if e is not None:
                self.events.add_event(
                    Event(type=Event.GAME,
                          name=Event.ACTION_SUCCEEDED,
                          description=f"You found {e.description}!"))

            # See if we changed rooms/tunnels
            if self.current_room != self.get_current_room():
                self.current_room = self.get_current_room()
                room_name = "a tunnel" if self.current_room is None else self.current_room.name
                self.events.add_event(
                    Event(type=Event.GAME,
                          name=Event.ACTION_SUCCEEDED,
                          description=f"You moved to {room_name}."))

        # Else raise an event
        else:

            # See if an entity blocked our way?
            e = self.get_entity_at_pos((self.player.x + dx, self.player.y + dy))
            if e is not None:
                print(e)
                print(e.properties)
                if e.get_property("IsEnemy"):
                    self.attack_entity(self.player, e)
                else:
                    self.events.add_event(
                        Event(type=Event.GAME,
                              name=Event.ACTION_FAILED,
                              description=f"{e.description} blocks your way!"))
            else:
                self.events.add_event(
                    Event(type=Event.GAME,
                          name=Event.ACTION_FAILED,
                          description=f"That way is blocked!"))

    def move_entity(self, entity: Entity, dx: int, dy: int) -> bool:

        success = True
        # If the destination is a valid path on the map...
        if self.walkable[entity.x + dx, entity.y + dy] > 0:
            # And no solid entity is blocking the way...
            e = self.get_entity_at_pos((entity.x + dx, entity.y+dy))
            if e is None or e.get_property("IsWalkable") == True:
                # Move the specified entity
                entity.move(dx, dy)
            else:
                success = False
        else:
            success = False

        return success

    def get_entity_at_pos(self, pos : tuple)->Entity:
        for e in self.entities:
            if e.xy == pos:
                return e
        return None

    def remove_entity(self, old_entity : Entity):
        if old_entity in self.entities:
            self.entities.remove(old_entity)
        else:
            print(f"Couldn't find {old_entity.name} on this floor!")


    def swap_entity(self, old_entity : Entity, new_entity : Entity = None):
        if old_entity in self.entities:
            if new_entity is not None:
                new_entity.xy = old_entity.xy
                self.entities.append(new_entity)

            self.entities.remove(old_entity)
        else:
            print(f"Couldn't find {old_entity.name} on this floor!")

    def attack_entity(self, attacker : Entity, target : Entity):

        self.events.add_event(
            Event(type=Event.GAME,
                  name=Event.ACTION_ATTACK,
                  description=f"{attacker.description} attacks {target.description}"))

        if random.randint(1,10) > 5:

            dmg = attacker.fighter.roll_damage()
            target.fighter.take_damage(dmg)

            self.events.add_event(
                Event(type=Event.GAME,
                      name=Event.ACTION_SUCCEEDED,
                      description=f"{attacker.description}'s {attacker.fighter.current_weapon.description} deals {dmg} damage"))

            if target.fighter.is_dead:
                target.state = Entity.STATE_DEAD
                attacker.fighter.add_kills()
                XP = target.fighter.get_XP_reward()
                attacker.fighter.add_XP(XP)
                corpse = EntityFactory.get_entity_by_name("Corpse")
                self.swap_entity(target, corpse)
                self.events.add_event(
                    Event(type=Event.GAME,
                          name=Event.ACTION_SUCCEEDED,
                          description=f"{attacker.description} kills {target.description} and gains {XP} XP"))
        else:
            self.events.add_event(
                Event(type=Event.GAME,
                      name=Event.ACTION_FAILED,
                      description=f"{attacker.description} swings at {target.description}...and misses!"))

    def get_current_room(self) -> Room:
        current_room = None

        for room in self.map_rooms.values():
            if room.contains_point(self.player.xy) is True:
                current_room = room
                break

        return current_room

    def add_map_room(self, new_room: Room) -> bool:
        """:param"""

        attempts = 10
        overlap = True

        # Shrink floor rect to allow for border
        floor_rect = self.rect.inflate(-2, -2)

        # Try a specified number of times to find a random space for the new room
        while overlap is True and attempts > 0:

            # Generate random centre
            cx = random.randint(floor_rect.left, floor_rect.right)
            cy = random.randint(floor_rect.top, floor_rect.bottom)
            new_room.rect.center = (cx, cy)

            # If the random room location fits within the floor boundaries...
            if floor_rect.contains(new_room.rect):
                overlap = False
                # Check to see if we arenot touching an existing room...
                for room in self.map_rooms.values():
                    if new_room.is_touching(room):
                        overlap = True
                        break

        # If we found a free space for the new room add it to the floor map
        if overlap is False:
            self.map_rooms[new_room.name] = new_room
            print(f'Added new room {new_room.name} at ({new_room.x},{new_room.y}) after {11 - attempts} attempts')

        return not overlap

    def run_room_check(self):
        for room1 in self.map_rooms.values():
            for room2 in self.map_rooms.values():
                if room1 is room2:
                    continue
                x = room1.is_touching(room2)

                print(f'room {room1.name} vs. room {room2.name}touching={x}')

    def build_floor_map(self):

        # Start with nothing explored!
        self.explored = np.zeros((self.width, self.height), dtype=bool)

        # Start with nothing walkable!
        self.walkable = np.zeros((self.width, self.height))

        # Make floor walkable where rooms are
        for room in self.map_rooms.values():
            x, y, w, h = room.rect
            self.walkable[x:x + w, y: y + h] = 1

        # Make floor walkable where tunnels are
        for tunnel in self.map_tunnels:
            for sx, sy in tunnel.get_segments():
                self.walkable[sx, sy] = 1

        # Convert walkable to array of bools
        self.walkable = self.walkable > 0

        # x, y, w, h = self.last_room.rect
        # self.explored[x:x + w, y: y + h] = 1


    def recompute_fov(self, x=None, y=None, radius=None, light_walls=True, algorithm=0):

        # Use the player's xy if non specified
        if x is None and self.player is not None:
            x = self.player.x
        if y is None and self.player is not None:
            y = self.player.y

        # Use floor's radius if nothing specified
        if radius is None:
            radius = self.fov_radius

        # Use libtcod to calculate field of view
        self.fov_map = libtcod.map.compute_fov(self.walkable,
                                               (x, y),
                                               radius,
                                               light_walls,
                                               algorithm)

        # Add FOV cells to explored cells
        self.explored |= self.fov_map

        return self.fov_map

    def get_walkable_cells(self):
        results = np.where(self.walkable > 0)
        return list(zip(results[0], results[1]))

    def get_explored_cells(self):
        results = np.where(self.explored > 0)
        return list(zip(results[0], results[1]))

    def get_fov_cells(self):
        results = np.where(self.fov_map > 0)
        return list(zip(results[0], results[1]))

    def tick(self):
        # current_fov = self.get_fov_cells()
        # for entity in self.entities:
        #     if entity.xy in current_fov and entity.get_property("IsEnemy") == True:
        #         print(f'Tick {entity.name}')
        dead_bots = []

        for bot in self.bots:
            bot.tick()
            if bot.is_dead is True:
                dead_bots.append(bot)

        for bot in dead_bots:
            print(f'Bot {bot} is dead')
            self.bots.remove(bot)



class Model():

    GAME_STATE_PAUSED = "paused"
    GAME_STATE_PLAYING = "playing"
    GAME_STATE_LOADED = "loaded"
    GAME_STATE_GAME_OVER = "game over"

    def __init__(self, name: str):
        # Properties of the game
        self.name = name
        self.dungeon_level = 0
        self.state = None

        # Contents of the game
        self.player = None
        self.inventory = {}
        self.entities = None
        self.floors=[]
        self.current_floor = None
        self.events = EventQueue()

    def initialise(self):

        EntityFactory.load("entities.csv")
        CombatClassFactory.load("combat_classes.csv")
        CombatEquipmentFactory.load("combat_equipment.csv")

        cc = CombatClassFactory.get_combat_class_by_name("Warrior")
        eq = EntityFactory.get_entity_by_name("Dagger")
        new_player = Player(name="Keith")
        new_player.fighter = Fighter(combat_class=cc)
        new_player.fighter.equip_item(eq)

        self.add_player(new_player)
        self.next_floor()
        self.set_state(Model.GAME_STATE_LOADED)

    def print(self):
        self.current_floor.print()

    def tick(self):
        if self.state == Model.GAME_STATE_PLAYING:
            self.current_floor.tick()

    def set_state(self, new_state):
        if new_state != self.state:
            self._old_state = self.state
            self.state = new_state

    def set_mode(self, new_mode):
        self.set_state(new_mode)

    def get_next_event(self)->Event:
        next_event = None
        if self.events.size() > 0:
            next_event = self.events.pop_event()
        return next_event

    def add_player(self, new_player: Player):
        self.player = new_player

    def get_current_player(self):
        return self.player

    def move_player(self, dx: int, dy: int):
        self.current_floor.move_player(dx, dy)

    def take_item(self)->bool:

        success = False

        # See if there is anything at your current position
        e = self.current_floor.get_entity_at_pos(self.player.xy)

        # If there are no entities at this location then fail
        if e is None:
            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.ACTION_FAILED,
                                        description=f"There is nothing here!"))

        # If there is an entity that you can pick-up then process it
        elif e.get_property("IsCollectable") == True:

            success = self.player.inventory.add_item(e)

            # If we manage to pick up an item then remove it from the floor
            if success is True:
                self.current_floor.swap_entity(e)
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.ACTION_SUCCEEDED,
                                            description=f"You picked up {e.description}!"))
            else:
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.ACTION_FAILED,
                                            description=f"You are unable to pick up {e.description}!"))


        # Otherwise you can't pick it up
        else:
            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.ACTION_FAILED,
                                        description=f"You can't pick up {e.description}!"))

        return success

    def take_stairs(self):

        # First see if there is anything at the current location.  If not then fail.
        e = self.current_floor.get_entity_at_pos(self.player.xy)
        if e is None:
            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.ACTION_FAILED,
                                        description=f"There is nothing here!"))

        # If we found down stairs go to next floor
        elif e.name == "Down Stairs":
            self.next_floor()

        # If we found up stairs go to teh previous floor
        elif e.name == "Up Stairs":
            self.previous_floor()

        # Else the entity at this space is not stairs!
        else:
            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.ACTION_FAILED,
                                        description=f"There are no stairs here!"))

    def previous_floor(self):
        self.dungeon_level -= 1

        # If we have not reached the top level...
        if self.dungeon_level > 0:

            # Get the floor
            self.current_floor = self.floors[self.dungeon_level - 1]

            # Add the player at the end of the previous level
            self.current_floor.add_player(self.player, first_room = False)

            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.GAME_NEW_FLOOR,
                                        description=f"{self.name}:'{self.current_floor.name}' at Level {self.dungeon_level} Ready!"))

        else:

            self.dungeon_level += 1

            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.ACTION_FAILED,
                                        description=f"There are no levels above this one!"))

    def next_floor(self):

            self.dungeon_level += 1

            # If the new level doesn't exist yet then create it...
            if self.dungeon_level > len(self.floors):

                # Create a new floor and initialise
                self.current_floor = Floor(f'The Floor {self.dungeon_level}', 50, 50, self.dungeon_level)
                self.current_floor.initialise(self.events)
                self.floors.append(self.current_floor)

            # Otherwise retrieve it
            else:
                self.current_floor = self.floors[self.dungeon_level-1]

            # Add the player at the start of teh new level
            self.current_floor.add_player(self.player)
            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.GAME_NEW_FLOOR,
                                        description=f"{self.name}:'{self.current_floor.name}' at Level {self.dungeon_level} Ready!"))

    def equip_item(self, new_item : Entity)->bool:

        success = False

        if new_item.get_property("IsEquipable") == True:
            success = self.player.equip_item(new_item)
            if success is True:
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.ACTION_SUCCEEDED,
                                            description=f"You equip {new_item.description}"))
        else:
            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.ACTION_FAILED,
                                        description=f"You can't equip {new_item.description}"))
        return success

    def drop_item(self, old_item : Entity)->bool:

        success = False

        e = self.current_floor.get_entity_at_pos(self.player.xy)
        if e is None:
            success = self.player.drop_item(old_item)
            if success is True:
                old_item.xy = self.player.xy
                self.current_floor.entities.append(old_item)
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.ACTION_SUCCEEDED,
                                            description=f"You drop {old_item.description} here"))
        else:
            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.ACTION_FAILED,
                                        description=f"You can't drop {old_item.description} here"))

        return success

    def use_item(self, new_item : Entity)->bool:

        success = False

        if new_item.get_property("IsInteractable") == True:
            success = self.player.drop_item(new_item)
            if success is True:
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.ACTION_SUCCEEDED,
                                            description=f"You use {new_item.description}"))
        else:
            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.ACTION_FAILED,
                                        description=f"You can't use {new_item.description}"))
        return success


import math

class AIBot:

    INSTRUCTION_FAIL_NOP = "NOP"
    INSTRUCTION_FAIL_TICK = "TICK"
    INSTRUCTION_FAIL_SKIP = "SKIP"
    INSTRUCTION_FAIL_VALID_OPTIONS = (INSTRUCTION_FAIL_NOP, INSTRUCTION_FAIL_SKIP, INSTRUCTION_FAIL_TICK)

    def __init__(self, name: str, bot_entity: Entity, floor: Floor, tick_slow_factor: int = 1):
        self.name = name
        self.bot_entity = bot_entity
        self.floor = floor
        self.tick_slow_factor = tick_slow_factor
        self.loop = False
        self.tick_count = 1
        self._debug = False

    @property
    def is_dead(self):
        return self.bot_entity.state == Entity.STATE_DEAD

    def debug(self, debug_on: bool = None):
        if debug_on is None:
            self._debug = not self._debug
        else:
            self._debug = debug_on

    def tick(self):
        self.tick_count += 1
        return self.tick_count % self.tick_slow_factor == 0

    def reset(self):
        self.tick_count = 0

    def distance_to_target(self, target: Entity):

        fx = self.bot_entity.x
        fy = self.bot_entity.y

        tx = target.x
        ty = target.y

        distance = math.sqrt((fx - tx) ** 2 + (fy - ty) ** 2)

        return distance

    def __str__(self):
        text = "Subject:{0} at {1}".format(self.bot_entity.name, str(self.bot_entity.xy))
        return text

class AIBotTracker(AIBot):

    def __init__(self, bot_entity: Entity, floor: Floor, tick_slow_factor: int = 1):

        super().__init__(str(__class__), bot_entity, floor, tick_slow_factor)

        self.target_entity = None
        self.navigator = None
        self.failed_ticks = 0
        self.failed_ticks_limit = 10

    def __str__(self):

        text = f"{self.name}: Bot {self.bot_entity.name} at {self.bot_entity.xy}:"
        if self.target_entity is not None:
            text += f'target:{self.target_entity.name}'

        return text

    def set_instructions(self, new_target: Entity, sight_range: int = 5, loop: bool = True):
        self.target_entity = new_target
        self.sight_range = sight_range
        self.loop = loop

    def tick(self):

        success = False

        # If it's not our turn or
        # We haven't got a target
        if super().tick() is False or \
                self.target_entity is None:
            return success

        # If we have had too many failed attempts at tracking the object then give-up
        if self.failed_ticks > self.failed_ticks_limit:
            self.failed_ticks = 0
            return success

        # See if we are close enough to the target and
        # Check that there is a direct path to it
        d = self.distance_to_target(self.target_entity)
        target_in_sight = d <= self.sight_range

        # If we can attack it....
        if d < 2:

            print(f'{self.bot_entity.name}: "I can attack you {self.target_entity.name}"')
            self.floor.attack_entity(self.bot_entity, self.target_entity)

        # if we can see it...
        elif target_in_sight:

            bx, by = self.bot_entity.xy
            tx, ty = self.target_entity.xy

            # Try and track the target's X position
            if tx != bx:
                if tx < bx:
                    self.floor.move_entity(self.bot_entity, -1,0)
                elif tx > bx:
                    self.floor.move_entity(self.bot_entity, 1, 0)

            # Try and track the target's Y position
            if ty != by:
                if ty < by:
                    self.floor.move_entity(self.bot_entity, 0, -1)
                elif ty > by:
                    self.floor.move_entity(self.bot_entity, 0, 1)

            # If we moved and are still in sight of the target then all good
            success = (bx,by) != self.bot_entity.xy or target_in_sight

            print(f'{self.bot_entity.name}: "I can see you {self.target_entity.name}"')


        if self._debug is True and self.failed_ticks >0:
            print("Failed {0} vs. limit {1}".format(self.failed_ticks, self.failed_ticks_limit   ))

        return success

    def reset(self):
        super().reset()
        self.failed_ticks = 0
