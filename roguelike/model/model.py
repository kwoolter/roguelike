import collections
import copy
import operator

import numpy as np
import pygame.rect as rect
import tcod as libtcod

from .combat import *
from .entity_factory import Entity, Player, EntityFactory, Fighter
from .entity_factory import Inventory
from .events import Event
from .game_parameters import GameParameters
from .themes import ThemeManager


def dim_rgb(rgb, dc: int):
    """
    Dim a colour by a specified amount
    :param rgb: the RGB colour that you want to dim
    :param dc: how much do you want to dim it by?
    :return: a libtcod.Color object with the dimmed RGB colour
    """
    try:

        r, g, b = rgb
        r = max(0, r - dc)
        g = max(0, g - dc)
        b = max(0, b - dc)
        return libtcod.Color(r, g, b)
    except Exception:
        print(f'problem trying to dim {rgb}')
        assert False

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

    STYLE_STRAIGHT = "straight"
    STYLE_STRAIGHT_FAT = "straight_fat"
    STYLE_CURVED = "curved"

    def __init__(self, start_pos, end_pos, direction=None, fg=libtcod.white, bg=libtcod.black, style=STYLE_STRAIGHT):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.style = style
        self.fg = fg
        self.bg = bg

        self.start_bg = self.bg
        self.end_bg = self.bg

        if direction is None:
            self.direction = random.choice(Tunnel.DIRECTIONS)
        else:
            self.direction = direction

    def print(self):
        print(f'Tunnel running from {self.start_pos} to {self.end_pos} using {self.direction}')

    def get_segments_thin(self)->list:

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

    def get_segments_fat(self)->list:
        segments = []

        start_x, start_y = self.start_pos
        end_x, end_y = self.end_pos

        hy = start_y if self.direction == Tunnel.DIRECTION_H_V else end_y
        vx = end_x if self.direction == Tunnel.DIRECTION_H_V else start_x

        for x in range(min(start_x, end_x), max(start_x, end_x) + 1):
            segments.append((x, hy))
            segments.append((x, hy+1))

        for y in range(min(start_y, end_y), max(start_y, end_y) + 1):
            segments.append((vx, y))
            segments.append((vx+1, y))

        return segments

    def get_segments_direct(self)->list:

        segments = []

        cx, cy = self.start_pos
        ex, ey = self.end_pos

        segments.append((cx,cy))

        while (cx,cy) != self.end_pos:

            if cx < ex:
                cx += 1
            elif cx > ex:
                cx -= 1
            segments.append((cx, cy))
            segments.append((cx, cy+1))
            segments.append((cx+1, cy))

            if cy < ey:
                cy += 1
            elif cy > ey:
                cy -= 1
            segments.append((cx, cy))
            segments.append((cx, cy + 1))
            segments.append((cx+1, cy))

        return segments


    def get_segments(self)->list:

        fn = random.choice([self.get_segments_direct, self.get_segments_fat, self.get_segments_thin])
        x = set(fn())
        return list(x)

    def get_segment_distances(self, segment:tuple):

        seg_x,seg_y = segment
        start_x, start_y = self.start_pos
        end_x, end_y = self.end_pos

        l0_start = abs(seg_x - start_x) + abs(seg_y - start_y)
        l0_end = abs(seg_x - end_x) + abs(seg_y - end_y)

        return l0_start, l0_end


class Room:
    def __init__(self, name: str, w:int, h:int, fg=libtcod.white, bg=libtcod.black):
        """

        :param name:
        :param w:
        :param h:
        :param fg:
        :param bg:
        """

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

    @property
    def area(self):
        return self.width * self.height

    def is_touching(self, other_room):
        return self.rect.colliderect(other_room.rect.inflate(2, 2)) > 0

    def contains_point(self, point):
        x, y = point
        return self.rect.collidepoint(x, y) > 0

    def get_random_pos(self, margin = 0)->tuple:
        """

        :param margin:
        :return:
        """

        # Force the margin to be less than half of the smallest room dimension
        margin=int(min(margin,min(self.width, self.height)/2))

        return (self.x + random.randint(margin,self.width-margin-1), self.y + random.randint(margin,self.height-margin-1))

    def print(self):
        print(f'Room {self.name} located at {self.rect}, colour:{self.bg}')


class Floor():

    EMPTY_TILE = "Empty"

    def __init__(self, name: str, width: int = 50, height: int = 50, level: int = 0, theme:str = "default", params = None):

        # Properties of this floor
        self.name = name
        self.theme = random.choice(list(ThemeManager.available_themes))
        #self.theme = "Dungeon"
        self.room_colours = ThemeManager.get_room_colours_by_theme(self.theme)

        self.width = width
        self.height = height
        self.level = level
        self.rect = rect.Rect(0, 0, width, height)

        self._debug = False

        # Floor generation parameters
        self.room_parameters = params["Room"]
        self.floor_parameters = params["Floor"]

        # Get the number of rooms we want to add to this floor
        self.room_count = self.floor_parameters["Room"]["Count"]

        # Get the Max XP of enemies allowed per room
        self.room_xp_cap = self.room_parameters["MaxXP"]["Count"]

        self.room_min_size = 4
        self.room_size_haircut = 0.75
        self.room_max_size = int(max(math.sqrt(self.width * self.height / self.room_count) * self.room_size_haircut, self.room_min_size))

        # Contents of the floor
        self.player = None
        self.first_room = None
        self.current_room = None
        self.last_room = None
        self.item_user = None

        self.map_rooms = []
        self.map_tunnels = []
        self.entities = []
        self.bots = []

        # Which parts of the floor are:-
        # - Walkable?
        # - Have already been explored?
        # - Are in the current FOV?
        # - Have a specific tile colour set?
        self.walkable = None
        self.explored = None
        self.fov_map = None
        self.fov_radius = 7
        self.fov_radius2 = self.fov_radius**2
        self.floor_tile_colours = None
        self._explored_rooms = set()
        self.entities_added = 0

        self.events = None

    def is_valid_xy(self, x:int, y:int):
        return x >= 0 and x < self.width and y >= 0 and y < self.height

    @property
    def revealed_entities(self):
        self._revealed_entities = list(set(self.entities) & set(self._revealed_entities))
        return self._revealed_entities


    def initialise(self, events: EventQueue):
        """
        Initialise the whole Floor object by:-
        - creating some random rooms on the Floor
        - joining the rooms together by tunnels
        - adding random entities to the rooms
        - adding random entities to the whole floor
        - building a map of the floor tile properties

        :param events: the event queue that the Floor object can use to report game events
        """

        self.events = events

        # Lists for storing rooms and tunnels that we want to add to the Floor
        self.map_rooms = []
        self.map_tunnels = []

        # Arrays to hold properties of each tile on the Floor
        self.walkable = None
        self.explored = None
        self.fov_map = None
        self.floor_tile_colours = None
        self._revealed_entities = []
        self._explored_rooms = set()

        # Build template that contains the list of entities that we want to add to each Room
        room_entities_template = []
        enames = self.room_parameters.keys()
        for ename in enames:
            emax = self.room_parameters[ename]['Count']
            eprob = self.room_parameters[ename]['Probability']
            if emax>0 and eprob>0:
                room_entities_template.append((ename,eprob,emax))

        print("*"*40)
        print(room_entities_template)

        # Build template that contains the list of entities that we want to add to the Floor
        # end their maximum count and probability of adding one
        floor_entities = []
        enames = self.floor_parameters.keys()
        for ename in enames:
            emax = self.floor_parameters[ename]['Count']
            eprob = self.floor_parameters[ename]['Probability']
            if emax>0 and eprob>0:
                floor_entities.append((ename,eprob,emax))

        print("*"*80)
        print(floor_entities)

        # List of floor tile colours that can be randomly assigned to a Tunnel
        valid_tunnel_colours = ThemeManager.get_tunnel_colours_by_theme(self.theme)

        # List of room names that we can randomly assign to a room
        room_names = ThemeManager.get_room_names_by_theme(self.theme)

        # Define initial values for the first and last room
        self.last_room = None
        self.first_room = None
        self.last_enemy=None

        for i in range(self.room_count):

            # If we ran out of room names then reload!
            if len(room_names) == 0:
                room_names = ThemeManager.get_room_names_by_theme(self.theme)

            # Get a random room name and remove it from the list so it cannot be reused
            room_name = random.choice(room_names)
            room_names.remove(room_name)
            room_name = ThemeManager.get_random_history("Room")

            # Create a new room of random name, size and tile colour
            new_room = Room(name=room_name,
                            w=random.randint(self.room_min_size, self.room_max_size),
                            h=random.randint(self.room_min_size, self.room_max_size),
                            bg=ThemeManager.get_random_room_colour_by_theme(self.theme))

            # If we were able to add the room to the map...
            if self.add_map_room(new_room) is True:

                # if this is not the first room then...
                if self.last_room is not None:

                    # Add some random entities to the room using a template or count and probability
                    room_entities = room_entities_template.copy()
                    room_entities.append(("Pillar", 25, int(new_room.area / 10)))
                    self.add_entities_to_room(new_room, entities=room_entities)

                    # Create a tunnel connecting back to the previous room
                    random_tunnel_colour = random.choice(valid_tunnel_colours)
                    new_tunnel = Tunnel(start_pos=self.last_room.center,
                                        end_pos=new_room.center,
                                        bg=random_tunnel_colour)

                    new_tunnel.start_bg = self.last_room.bg
                    new_tunnel.end_bg = new_room.bg

                    self.map_tunnels.append(new_tunnel)

                # Make the new room the last room
                self.last_room = new_room

            else:
                print('\t**Couldnt add room so skipping and moving on')

        # redefine first and last rooms
        self.last_room = self.map_rooms[-1]
        self.first_room = self.map_rooms[0]
        self.last_room.name = "the Dungeon Exit"
        self.first_room.name = "the Dungeon Entrance"

        # Add random entities to the whole floor
        self.add_entities_to_floor(entities = floor_entities)

        # Build a map of the floor
        self.build_floor_map()

        # Randomly use cavern floor layout
        if random.randint(0,10) > 8 and self.level > 3:
            self.build_floor_cave(tile_colour= ThemeManager.get_random_room_colour_by_theme(self.theme))
            self.map_rooms = [self.first_room, self.last_room]

        self.entities_added = len(self.entities)

        self.item_user = ItemUser()
        self.item_user.initialise()

    def print(self):
        print(f'Floor {self.name}: ({self.width},{self.height})')
        for room in self.map_rooms:
            room.print()

        for tunnel in self.map_tunnels:
            tunnel.print()

        self.get_stats()

    def get_stats(self):
        stats_text = []

        rooms = len(self.map_rooms)
        rooms_explored = len(self._explored_rooms)
        rooms_explored_pct = rooms_explored * 100/ rooms

        stats_text.append(f"Rooms explored={rooms_explored_pct:0.0f}%")

        tiles = np.count_nonzero(self.walkable)
        tiles_explored = np.count_nonzero((np.logical_and(self.walkable,self.explored)))
        tiles_explored_pct = tiles_explored*100/tiles

        stats_text.append(f"Tiles explored={tiles_explored_pct:0.0f}%")

        return stats_text

    def get_XP_reward(self) -> int:
        reward = 0

        rooms = len(self.map_rooms)
        rooms_explored = len(self._explored_rooms)
        reward += int(rooms_explored * 100/ rooms)

        tiles = np.count_nonzero(self.walkable)
        tiles_explored = np.count_nonzero((np.logical_and(self.walkable,self.explored)))
        reward += int(tiles_explored*100/tiles)

        return reward


    def add_player(self, new_player: Player, first_room = True):

        if first_room is True:
            x, y = self.first_room.center
        else:
            x, y = self.last_room.center

        self.player = new_player
        self.player.xy = (x, y)
        self.move_player(0, 0)
        #self.entities.append(self.player)

        # Update FOV range with the player's combat class sight range
        self.fov_radius = new_player.combat_class.get_property("SightRange")
        self.fov_radius2 = self.fov_radius**2

        # Point all bots at the player!!!!
        for bot in self.bots:
            bot.set_instructions(new_target=self.player)
            print(bot)

    def add_entities_to_room(self, room : Room, entities):
        """
        Using a specified template add some random entities to a specified Room object
        :param room: the Room object that you want to add entities to
        :param entities: a list of tuples that each specifies entity name, entity probability and max entity count
        """

        enemy_xp_total = 0

        # loop through the entities that we are randomly deploying
        for ename, eprob, emax in entities:

            # If nothing to add for this entity loop to the next one
            if emax == 0 or eprob == 0:
                continue

            # Get a sample of the entity that we are trying deploy
            e=EntityFactory.get_entity_by_name(ename)

            if e is not None:
                template = e.get_property("Template")
                if template is not None:
                    print(f'Using entity template {template} for {e.description}')
                    # TBC to lookup template tprob and tcount !!!!
            else:
                continue

            # If the entity is an enemy and we have already hit the XP cap then loop to next entity
            if e.get_property("IsEnemy") == True and enemy_xp_total >= self.room_xp_cap:
                print(f'XP at {enemy_xp_total} which exceeds cap of {self.room_xp_cap}')
                continue

            # If it is solid and it doesn't move...
            # ...then avoid putting it around the edge of the room where it might block a tunnel!
            if e.get_property("IsWalkable") == False and \
                e.get_property("IsEnemy") == False:
                margin = 1

            else:
                margin = 0

            # Try an create a random number of entities up to the max allowable...
            for count in range(random.randint(1,emax)):

                # I random number less than our probability of creating this entity...
                if random.randint(1,100) < eprob:

                    # Find a random spot in the room
                    rx,ry = room.get_random_pos(margin=margin)

                    # If it is unoccupied...
                    if self.get_entity_at_pos((rx,ry)) is None:

                        # Place a new entity at this location
                        new_entity = EntityFactory.get_entity_by_name(ename)
                        new_entity.xy = rx,ry
                        self.entities.append(new_entity)

                        # if the entity is an enemy then create an AI bot to control it
                        if new_entity.get_property("IsEnemy") == True:
                            cc = CombatClassFactory.get_combat_class_by_name(new_entity.name)

                            assert cc is not None,f'Trying to add an enemy {new_entity.name} that does not have a Combat Class set-up'

                            enemy_xp_total += cc.get_property("XP")
                            self.generate_new_enemy(new_entity)
                            new_bot = AIBotTracker(new_entity, self)
                            self.bots.append(new_bot)

    def generate_new_enemy(self, new_entity : Entity):
        """
        Add Fighter characteristics to an Entity
        :param new_entity: the entity that we want to turn into a Fighter
        """

        cc = CombatClassFactory.get_combat_class_by_name(new_entity.name)
        new_fighter = Fighter(combat_class=cc)
        new_entity.fighter = new_fighter

    def add_entities_to_floor(self, entities: dict):

        # Add the player
        if self.player is not None:
            self.add_player(self.player)

        # Get list of all rooms on this floor but exclude the first and last rooms
        available_rooms = self.map_rooms[1:-2]

        # Add different stuff to random rooms across the floor
        for ename, eprob, emax in entities:
            print(f'Attempting to add {emax} {ename}s with prob={eprob}')

            # If nothing to add for this entity loop to the next one
            if emax == 0 or eprob == 0:
                continue

            # Get an entity of the named type
            e = EntityFactory.get_entity_by_name(ename)

            # If it is solid and it doesn't move...
            # ...then avoid putting it around the edge of the room where it might block a tunnel!
            if e.get_property("IsWalkable") == False and \
                    e.get_property("IsEnemy") == False:
                margin = 1
                print(f"margin = 1 for {e.name}:{e.description}")
            else:
                margin = 0

            # Attempt to add a random number of entities up to the max count per floor
            #for i in range(random.randint(1,emax)):
            for i in range(emax):

                # If random number less than our probability of creating this entity...
                if random.randint(1, 100) < eprob:

                    # pick a random room and a random position in the room
                    room=random.choice(available_rooms)

                    if e.name == "Shop":
                        room = self.first_room

                    rx, ry = room.get_random_pos(margin=margin)

                    # If there is nothing already there...
                    if self.get_entity_at_pos((rx, ry)) is None:

                        # Add a new entity to the floor at this location
                        new_entity = EntityFactory.get_entity_by_name(ename)
                        if new_entity is None:
                            print(f"Couldn't create entity by name of {ename}")
                            continue
                        new_entity.xy = rx,ry
                        self.entities.append(new_entity)

                        print(f'\t++ Added {new_entity.name} to room {room.name}')

                        # Don't use this room again
                        # Can't delete while iterating!!!!!
                        #available_rooms.remove(room)

        # If we are not at the top level add stairs back up to the previous level in the centre of the first room
        if self.level > 1:
            ename = "Up Stairs"
            new_entity = EntityFactory.get_entity_by_name(ename)
            new_entity.xy = self.first_room.center
            e = self.get_entity_at_pos(self.last_room.center)
            # Replace anything that is already there!
            if e is not None:
                self.remove_entity(e)

            # Not allowing to go back up a level at the moment unless in debug mode
            if self._debug is True:
                self.entities.append(new_entity)

        # In the last room add some stairs to the next level down
        ename = "Down Stairs"
        new_entity = EntityFactory.get_entity_by_name(ename)
        new_entity.xy = self.last_room.center
        e = self.get_entity_at_pos(self.last_room.center)
        # Replace anything that is already there!
        if e is not None:
            self.remove_entity(e)
        self.entities.append(new_entity)

    def move_player(self, dx, dy, relative:bool =True)->bool:
        """
        Attempt to move the Player on the Floor
        :param dx: change in x position
        :param dy: change in y position
        :return: True if the Player actually moved otherwise False
        """
        # If the player moved...
        moved = self.move_entity(self.player, dx, dy, relative)
        if moved is True:

            # Recalculate their current FOV using sight radius of combat class
            self.recompute_fov(radius = self.player.fighter.combat_class.get_property("SightRange"))

            # See if we found something?
            e = self.get_entity_at_pos(self.player.xy)
            if e is not None:
                self.events.add_event(
                    Event(type=Event.GAME,
                          name=Event.ACTION_FOUND_ITEM,
                          description=f"You found {e.description}!"))

            # See if we changed rooms/tunnels
            if self.current_room != self.get_current_room():
                self.current_room = self.get_current_room()
                if self.current_room is None:
                    room_name = "a tunnel"
                else:
                    room_name = self.current_room.name
                    self._explored_rooms.add(self.current_room)

                self.events.add_event(
                    Event(type=Event.GAME,
                          name=Event.ACTION_SUCCEEDED,
                          description=f"You moved to {room_name}."))

        # Else see why we couldn't move..
        else:

            # See if an entity blocked our way?
            e = self.get_entity_at_pos((self.player.x + dx, self.player.y + dy))
            if e is not None:

                # If it is an enemy then attack it
                if e.get_property("IsEnemy"):
                    self.attack_entity(self.player, e)
                    self.last_enemy = e

                # Else if you can ability check with the entity...
                elif e.get_property("IsCheckable"):
                    self.run_ability_check(e)

                # Else raise event about what entity is blocking you
                else:
                    self.events.add_event(
                        Event(type=Event.GAME,
                              name=Event.ACTION_FAILED,
                              description=f"{e.description} blocks your way!"))

            # Otherwise the way is blocked for another reason
            else:
                self.events.add_event(
                    Event(type=Event.GAME,
                          name=Event.ACTION_FAILED,
                          description=f"That way is blocked!"))

        return moved

    def move_entity(self, entity: Entity, dx: int, dy: int,
                    relative:bool = True,
                    include_player:bool = False) -> bool:
        """
        Attempt to move a specified Entity across the Floor
        :param entity: the Entity object that you want to move
        :param dx: the change in x position
        :param dy: the change in y position
        :return: True if we succeeded in moving teh Entity otherwise Falee
        """
        success = True

        if relative is False:
            entity.xy = [0,0]

        newx = entity.x + dx
        newy = entity.y + dy

        # If the destination is a valid path on the map...
        if self.walkable[newx,newy] > 0:

            # And no solid entity is blocking the way...
            e = self.get_entity_at_pos((newx,newy))
            if e is None or e.get_property("IsWalkable") == True:

                # ..or the player is not blocking
                if include_player is False or (newx,newy) != self.player.xy:
                    # Move the specified entity
                    entity.move(dx, dy)

            # Something is blocking the way so fail
            else:
                success = False

        # Otherwise we can't walk to the new destination so fail
        else:
            success = False

        return success

    def get_entity_at_pos(self, pos : tuple, include_player = False)->Entity:
        """
        See if there is an Entity object occupying a specified xy position on the Floor
        :param pos: the xy position that you want to check
        :return: the Entity at the specified position if one was found otherwise None.  if more then one found sort by Z order
        """
        found = []
        for e in self.entities:
            if e.xy == pos and (include_player is True or e is not self.player):
                found.append(e)

        if len(found)>0:
            found.sort(key=lambda x: x.get_property("Zorder"),reverse=False)
            e = found[0]
        else:
            e = None

        return e

    def remove_entity(self, old_entity : Entity):
        if old_entity in self.entities:
            self.entities.remove(old_entity)
        else:
            print(f"Couldn't find {old_entity.name} on this floor!")


    def swap_entity(self, old_entity : Entity, new_entity : Entity = None):
        """
        Swap an entity on the floor with a new entity
        :param old_entity: the entity that you want to swap out
        :param new_entity: the new entity that you want to replace it with. Default is None which means remove the old entity
        """
        if old_entity in self.entities:
            if new_entity is not None and new_entity.name != Floor.EMPTY_TILE:
                new_entity.xy = old_entity.xy
                self.entities.append(new_entity)
            self.entities.remove(old_entity)
        else:
            print(f"Couldn't find {old_entity.name} on this floor!")

    def attack_entity(self, attacker : Entity, target : Entity, weapon : CombatEquipment = None):
        """
        Process an attacker performing an attack on a target.  The process is:-
        - Did the attack succeed?
        - If it did what damage did it inflict?
        - Did the attack kill the target Entity?

        :param attacker: the Entity that is attacking
        :param target: The Entity that is the target of the attack
        """
        self.events.add_event(
            Event(type=Event.DEBUG,
                  name=Event.ACTION_ATTACK,
                  description=f"{attacker.description} attacks {target.description}"))

        attacker.fighter.last_target = target

        # What weapon are we using for the attack?
        if weapon is None:
            weapon = attacker.fighter.current_weapon_details

        # What are the attack and defence abilities for this weapon?
        attack_ability = weapon.get_property("ATK")
        defence_ability = weapon.get_property("DEF")

        # Roll a 20 sided dice and add to attack power
        attack = attacker.fighter.get_attack(attack_ability) + random.randint(1,20)

        # Calculate the target's ability defence
        defence = target.fighter.get_defence(defence_ability)

        print(f'{attacker.name} using weapon {weapon.description} ({attack_ability} vs {defence_ability})')
        print(f'{attacker.name} ATK ({attack_ability}={attack}) vs ({defence_ability}={defence}) DEF of {target.name}')
        print(f'Defender HP={target.fighter.combat_class.get_property("HP")}')

        # Did the attack succeed...?
        if attack > defence:

            # Target out of range???
            d = attacker.distance_to_target(target)

            if d > weapon.get_property("Range"):
                self.events.add_event(
                    Event(type=Event.GAME,
                          name=Event.ACTION_FAILED,
                          description=f"{target.description.capitalize()} is out of range for {weapon.description}"))

            else:

                # Roll some damage based on the attackers weapon + attack modifier and deduct damage from target's HP
                dmg = weapon.get_damage_roll() + max(0,attacker.fighter.get_attack(attack_ability))

                target.fighter.take_damage(dmg)

                # Strip of the first word of the weapon description
                # e.g 'a small dagger' -> 'small dagger'
                weapon_name = weapon.description[weapon.description.find(' ')+1:]

                self.events.add_event(
                    Event(type=Event.GAME,
                          name=Event.ACTION_ATTACK,
                          description=f"{attacker.description.capitalize()} deals {dmg} damage with {weapon.description}"))

                # If the target died...
                if target.fighter.is_dead:
                    target.state = Entity.STATE_DEAD

                    # Update attacker stats
                    attacker.fighter.add_kills()
                    XP = target.fighter.get_XP_reward()
                    attacker.fighter.add_XP(XP)
                    attacker.fighter.last_target = None

                    # Swap the target on the floor to a corpse
                    corpse = EntityFactory.get_entity_by_name("Corpse")
                    self.swap_entity(target, corpse)

                    self.events.add_event(
                        Event(type=Event.GAME,
                              name=Event.ACTION_SUCCEEDED,
                              description=f"{attacker.description.capitalize()} kills {target.description}."))

                    self.events.add_event(
                        Event(type=Event.GAME,
                              name=Event.ACTION_GAIN_XP,
                              description=f"{attacker.description.capitalize()} gains {XP} XP"))


        # The attack failed...
        else:
            self.events.add_event(
                Event(type=Event.GAME,
                      name=Event.ACTION_FAILED,
                      description=f"{attacker.description.capitalize()} swings at {target.description} and misses!"))

    def run_ability_check(self, e:Entity):
        """
        See if there any ability checks for the specified object and run them
        :param e: the Entity that you want to perform a check on
        :return: did the check succeed of Fail?
        """

        success = False

        # See of there any ability checks for the specified Entity
        checks = AbilityChecksFactory.get_entity_ability_checks(e.name)

        # If there are more than one type of check for this entity...
        if len(checks) > 1:

            # Build a list to see which ability check we are most likely to succeed at...
            stats = []
            for ability, check in checks.items():
                # Get the ability modifier that is appropriate for the ability check
                ability_modifier = self.player.fighter.get_property_modifier(check.ability)
                stats.append((ability, check.difficulty_value - ability_modifier))

            stats.sort(key=operator.itemgetter(1))
            print(stats)
            # Pick the ability that has the lowest diffculty score
            ability, score = stats[0]
            print(f'Chosen check = {stats[0]}')

        elif len(checks) == 1:
            ability = list(checks.keys())[0]
        else:
            ability = "NONE"

        check = checks.get(ability)

        # If we found an ability check....
        if check is not None:

            print(str(check))
            # Make this entity non-checkable going forward!
            # You get one go at attempting the check!
            e.set_property("IsCheckable", False)

            # Get the ability modifier that is appropriate for the ability check
            ability_modifier = self.player.fighter.get_property_modifier(check.ability)

            # Print the description of the check
            if check.description is not None:
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.ACTION_SUCCEEDED,
                                            description=check.description))

            # Attempt the ability check
            success = check.attempt(ability_modifier)

            # If we succeeded...
            if success is True:

                # Print success message
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.ACTION_SUCCEEDED,
                                            description=check.success_msg))

                # See if we got a reward item
                if check.success_reward is not None:
                    self.swap_entity(e, check.success_reward)

                    if check.success_reward != Floor.EMPTY_TILE:
                        self.events.add_event(Event(type=Event.GAME,
                                                    name=Event.EFFECT_ITEM_DISCOVERY,
                                                    description=f'You find {check.success_reward.description}'))

                for k,v in check.success_misc.items():
                    if k == "History":
                        text = ThemeManager.get_random_history(v)
                        self.events.add_event(
                            Event(type=Event.GAME,
                                  name=Event.ACTION_FOUND_LORE,
                                  description=f"[Lore] {v}:'{text}'"))

                # Update any stats with any rewards
                for stat, value in check.success_stats.items():
                    if stat == "HP":
                        if value > 0:
                            self.player.heal(value)
                            self.events.add_event(
                                Event(type=Event.GAME,
                                      name=Event.GAIN_HEALTH,
                                      description=f"You recover {value} HP"))
                        else:
                            self.player.take_damage(value)
                            self.events.add_event(
                                Event(type=Event.GAME,
                                      name=Event.LOSE_HEALTH,
                                      description=f"You lose {abs(value)} some HP"))
                    elif stat == "XP":
                        self.player.fighter.add_XP(value)
                        self.events.add_event(
                            Event(type=Event.GAME,
                                  name=Event.ACTION_GAIN_XP,
                                  description=f"You gain {value} XP"))
                    else:
                        print(f'get reward {stat}={value} but did nothing!')




            # If ability check failed...
            else:

                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.ACTION_FAILED,
                                            description=check.failure_msg))

                # See if we got a failure reward item
                if check.failure_reward is not None:
                    self.swap_entity(e, check.failure_reward)

                # Update any stats with any failure rewards
                for stat, value in check.failure_stats.items():
                    if stat == "HP":
                        if value > 0:
                            self.player.heal(value)
                            self.events.add_event(
                                Event(type=Event.GAME,
                                      name=Event.GAIN_HEALTH,
                                      description=f"You recover {value} HP"))
                        else:
                            self.player.take_damage(abs(value))
                            self.events.add_event(
                                Event(type=Event.GAME,
                                      name=Event.LOSE_HEALTH,
                                      description=f"You lose {abs(value)} HP"))
                    elif stat == "XP":
                        self.player.fighter.add_XP(value)
                        self.events.add_event(
                            Event(type=Event.GAME,
                                  name=Event.ACTION_GAIN_XP,
                                  description=f"You gain {value} XP"))
                    else:
                        print(f'get reward {stat}={value} but did nothing!')


        # No ability checks found for this Entity
        else:
            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.ACTION_FAILED,
                                        description="Nothing happens"))

        return success

    def get_current_room(self, xy:tuple = None) -> Room:
        """
        See if a specified point on the Floor map is within a room
        :param xy: the point that you want to check. Default is the player's current position
        :return: the Room object that you are in or None if you are not in a Room
        """

        # If you didn't specify an xy position then use the player's current position
        if xy is None:
            xy = self.player.xy

        current_room = None

        # Loop through the rooms to see if teh specified point is an a room
        for room in self.map_rooms:
            if room.contains_point(xy) is True:
                current_room = room
                break

        return current_room

    def add_map_room(self, new_room: Room) -> bool:
        """
        Attemple to add a new room to the Floor map
        :param new_room: the new Room that you want to add
        :return: True if successfully added
        """

        # How many times do we attempt to add the room before giving up?
        attempts = 20

        # Shrink available floor rect so that rooms don't get placed right on the edge of the map
        floor_rect = self.rect.inflate(-2, -2)

        # Try a specified number of times to find a random space for the new room
        overlap = True

        while overlap is True and attempts > 0:

            # Generate random centre for the new room
            cx = random.randint(floor_rect.left, floor_rect.right)
            cy = random.randint(floor_rect.top, floor_rect.bottom)
            new_room.rect.center = (cx, cy)

            # If the random room location fits within the floor boundaries...
            if floor_rect.contains(new_room.rect):
                overlap = False
                # Check to see if we are not touching an existing room...
                for room in self.map_rooms:
                    # If we touched an existing room then try again!
                    if new_room.is_touching(room):
                        overlap = True
                        break

            attempts -= 1

        # If we found a free space for the new room add it to the floor map
        if overlap is False:
            self.map_rooms.append(new_room)
            print(f'Added new room {new_room.name} at ({new_room.x},{new_room.y}) after {21 - attempts} attempts')
        else:
            print("Failed to Add room")

        return not overlap

    def run_room_check(self):
        for room1 in self.map_rooms:
            for room2 in self.map_rooms:
                if room1 is room2:
                    continue
                x = room1.is_touching(room2)

                print(f'room {room1.name} vs. room {room2.name}touching={x}')

    def build_floor_map(self):
        """
        Build arrays the represent different properties of each floor til in the Floor.  The arrays are:-
        - walkable - can you walk on a tile?
        - explored - have you seen this tile yet?
        - floor_tile_colours - the colour of each floor tile
        """
        assert self.first_room in self.map_rooms
        assert self.last_room in self.map_rooms

        # Start with nothing explored!
        self.explored = np.zeros((self.width, self.height), dtype=bool)

        # Start with nothing walkable!
        self.walkable = np.zeros((self.width, self.height))

        # Start with no fg and bg colours specified
        self.floor_tile_colours = np.full((self.width, self.height, 3), 0)

        # Make floor walkable where tunnels are and store the floor tile colour
        for tunnel in self.map_tunnels:
            segments = tunnel.get_segments()

            for sx, sy in segments:
                if self.is_valid_xy(sx,sy):

                    start_l0, end_l0 = tunnel.get_segment_distances((sx,sy))
                    total_l0 = start_l0 + end_l0
                    from_start_pct = start_l0/total_l0
                    from_end_pct = end_l0/total_l0

                    self.walkable[sx, sy] = 1
                    self.floor_tile_colours[sx,sy] = list(tunnel.bg)
                    self.floor_tile_colours[sx, sy] = libtcod.color_lerp(tunnel.start_bg, tunnel.end_bg, from_start_pct)

        # Make floor walkable where rooms are and store any floor tile colours
        for room in self.map_rooms:
            x, y, w, h = room.rect
            self.walkable[x:x + w, y: y + h] = 1
            # if random.randint(0,10) > 5:
            #     self.walkable[x, y] = 0
            #     self.walkable[x + w - 2, y] = 0
            #     self.walkable[x, y + h - 2] = 0
            #     self.walkable[x + w - 2, y + h - 2] = 0

            self.floor_tile_colours[x:x + w, y: y + h] = list(room.bg)

        # Convert walkable to array of bools
        self.walkable = self.walkable > 0

    def build_floor_cave(self, tile_colour, reset:bool = False):
        """
        Build arrays the represent different properties of each floor til in the Floor.  The arrays are:-
        - walkable - can you walk on a tile?
        - explored - have you seen this tile yet?
        - floor_tile_colours - the colour of each floor tile
        """
        assert self.first_room in self.map_rooms
        assert self.last_room in self.map_rooms

        # Rest everything if requested to
        if reset is True:

            # Start with nothing explored!
            self.explored = np.zeros((self.width, self.height), dtype=bool)

            # Start with nothing walkable!
            self.walkable = np.zeros((self.width, self.height))

        other_walkable = np.zeros((self.width, self.height))

        # Start with no fg and bg colours specified then populate with specified tile colour
        self.floor_tile_colours = np.full((self.width, self.height,3), 0)
        self.floor_tile_colours[:,:] = list(tile_colour)

        # Make a column with random walkable middle areas and some random non-walkable points
        for x in range(1,self.width-1):
            other_walkable[x, 2+ random.randint(0,5):self.height-2 - random.randint(0,5)] = 1
            other_walkable[x] = np.logical_and(other_walkable[x], random.choices([0,1],[10,90], k=self.height))

        # Make row with random non-walkable edges
        for y in range(2,self.height-4):
            other_walkable[:random.randint(0,5),y] = 0
            other_walkable[random.randint(-5, -1):, y] = 0

        # Logical OR of current walkable grid and the random cave grid
        self.walkable = np.logical_or(self.walkable, other_walkable)

    def reveal_map(self, only_exit = False):
        """
        Reveal  parts of the Floor map by "exploring" them
        :param only_exit:
        """
        if only_exit is True:
            # Show where the final room of the floor is (CHEAT)
            x, y, w, h = self.last_room.rect
            self.explored[x:x + w, y: y + h] = 1

        # Explore the WHOLE map
        else:
            self.explored[:,:] = 1

        # Show the stairs down to teh next level
        self.reveal_entities_by_name("Down Stairs")

    def reveal_entities_by_property(self, property_name: str, probability: int = 100):
        """
        Randomly reveal all entities on this Floor that have a property and value matching those specified
        :param property_name:
        :param probability: probability of success for each entity that matches
        """
        self._revealed_entities = list(set(self.entities) & set(self._revealed_entities))
        for e in self.entities:
            if e.get_property(property_name) == True and random.randint(1, 100) <= probability:
                self._revealed_entities.append(e)


    def reveal_entities_by_name(self, entity_name: str, probability: int = 100):
        """
        Randomly reveal entities that have a specified name
        :param entity_name: name of entities to be revealed
        :param probability: probability of success for each entity that matches
        """
        self._revealed_entities = list(set(self.entities) & set(self._revealed_entities))
        for e in self.entities:
            if e.name == entity_name and random.randint(1, 100) <= probability:
                self._revealed_entities.append(e)

    def swap_entities_by_name(self, entity_name: str, new_entity_list, probability: int = 100):
        """
        Randomly swap entities of a specified name with  a random list of new entities
        :param entity_name: name of the entity to swap
        :param new_entity_list: the list of entity names to swap it with
        :param probability: the probability of a successful swap happening for each matching entity
        """
        for e in self.entities:
            if e.name == entity_name and random.randint(1, 100) <= probability:
                new_entity = EntityFactory.get_entity_by_name(random.choice(new_entity_list))
                self.swap_entity(e, new_entity)
                print(f'\tyou swap {entity_name} for {new_entity.name}')

    def recompute_fov(self, x=None, y=None, radius=None, light_walls=True, algorithm=0):
        """
        Update the Field of View numpy array and teh explored array based on:-
        :param x: x position on Floor.  Default use player's x
        :param y: y position on Floor.  Default use player's y
        :param radius: radius of the Field of View.  Defult use the class default
        :param light_walls: Are list walls included in the FOV results?
        :param algorithm:
        :return: the updated FOV map in np as an numpy array
        """
        # Use the player's xy if non specified
        if x is None and self.player is not None:
            x = self.player.x
        if y is None and self.player is not None:
            y = self.player.y

        # Use floor's radius if nothing specified
        if radius is None:
            radius = self.fov_radius

        walkable = self.walkable.copy()
        for e in self.entities:
            if e.get_property("IsTransparent") == False:
                walkable[e.x,e.y] = False

        # Use libtcod librarty function to calculate field of view
        self.fov_map = libtcod.map.compute_fov(walkable,
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

    def get_fov_light_attenuation(self, ox: int, oy:int, factor:float = 1.0):
        px, py = self.player.xy
        return factor * ((px-ox)**2 + (py-oy)**2) / self.fov_radius2

    def get_revealed_entities(self):
        return self.revealed_entities


    def tick(self):
        """
        Do a tick on this Floor
        """
        dead_bots = []

        # Tick all bots and collect any dead ones
        for bot in self.bots:
            bot.tick()
            if bot.is_dead is True:
                dead_bots.append(bot)

        # Remove any dead bots
        # (can't remove and iterate at the same time!)
        for bot in dead_bots:
            print(f'Bot {bot} is dead')
            self.bots.remove(bot)

class Shop():

    def __init__(self, name: str = "default shop"):
        # Properties
        self.name = name

        # Components
        self.floor = None
        self.category_to_entity = {}

    def initialise(self, floor: Floor):

        # Store the new shop floor and update name of the shop
        self.floor = floor
        self.name = f'The Shop on Level {self.floor.level}'

        # Get the list of tradable entities and sort them alphabetically
        self.buy_list = [e for e in self.floor.entities if e.get_property("IsTradable") == True]
        self.buy_list.sort(key=operator.attrgetter('description'))

        self.build_items_by_category()

    def build_items_by_category(self):
        # Build a map of Entity category to list of matching Entities
        for item in self.buy_list:
            key = item.category
            if key not in self.category_to_entity:
                self.category_to_entity[key] = []
            self.category_to_entity[key].append(item)

    def get_buy_list(self):
        return self.buy_list
    
    def buy_item(self, item: Entity):
        self.buy_list.remove(item)
        self.build_items_by_category()

    def sell_item(self, item: Entity):
        self.buy_list.append(item)
        self.buy_list.sort(key=operator.attrgetter('description'))
        self.build_items_by_category()
        


class Model():
    """
    Description:
    The class contains the model for the WHOLE game.
    """

    GAME_STATE_PAUSED = "paused"
    GAME_STATE_PLAYING = "playing"
    GAME_STATE_LOADED = "loaded"
    GAME_STATE_GAME_OVER = "game over"

    def __init__(self, name: str):
        """:arg name the name that you want to give to this game
        """

        # Properties of the game
        self.name = name
        self.dungeon_level = 0
        self.state = None

        # Contents of the game
        self.player = None
        self.inventory = {}
        self.entities = None
        self.ability_checks = None
        self.floors=[]
        self.current_floor = None
        self.shop = None
        self.events = EventQueue()
        self.item_user = None

    def initialise(self):
        """
        Initialise an instance of the Model.

        """

        # Load game data from specified files
        ThemeManager.load_room_names("room_names.csv")
        ThemeManager.load_history_data("rogue_history.cfg")
        ThemeManager.load_room_colour_palettes("room_palettes.csv")
        ThemeManager.load_floor_colour_palettes("floor_palettes.csv")
        GameParameters.load("game_parameters.csv")
        EntityFactory.load("entities.csv")
        AbilityChecksFactory.load("ability_checks.csv")
        CombatClassFactory.load("combat_classes.csv")
        CombatEquipmentFactory.load("combat_equipment.csv")

        if self.player is None:
            self.add_player(self.generate_player(name="Keith", class_name="Rogue"))

        self.next_floor()
        self.set_state(Model.GAME_STATE_LOADED)

        self.item_user = ItemUser()
        self.item_user.initialise()

        random_categories = ("Potion", "Scroll")
        for category in random_categories:
            entities = EntityFactory.get_entities_by_category(category)
            self.item_user.add_randomiser_group(category, entities)

        self.item_user.randomise()

        self.shop = Shop(f'{self.name} Shop')
        self.shop.initialise(self.current_floor)


    def load_game_parameters(self, level=1, XP=0)->dict:
        """

        :return:
        """

        # Dictionary to store the calculated Room, Floor and Game parameters
        game_parameters = {"Room":{},
                           "Floor":{},
                           "Game":{}}

        # Current inputs required for the calculations
        current_input = { "Level" : self.dungeon_level,
                          "XP" : self.player.get_property("XP")}

        #For each of the Room and Floor level parameters
        for scope in game_parameters.keys():

            # Get the list of parameters that we need to calculate
            scope_parameters = list(GameParameters.get_parameters_by_scope(scope))

            # For each parameter...
            for yname, ymetric in scope_parameters:

                # Get the name of the x input parameter that we need for y=f(x)
                xname = GameParameters.get_parameter_input(yname, ymetric)

                # Calculate y value based on x value
                yvalue = int(GameParameters.get_parameter(yname, ymetric, current_input[xname]))

                # Store yname, ymetric and yvalue in our results dictionary
                if yname not in game_parameters[scope].keys():
                    game_parameters[scope][yname]={}
                game_parameters[scope][yname][ymetric] = yvalue

            print(game_parameters)

        #assert False

        return game_parameters

    def print(self):
        self.current_floor.print()

    def debug(self):
        self.player.print()
        self.print()
        r = self.current_floor.get_current_room()
        if r is not None:
            self.current_floor.get_current_room().print()

    def tick(self):
        if self.state == Model.GAME_STATE_PLAYING:
            self.current_floor.tick()

        if self.player.fighter.is_dead == True:

            if self.player.get_property("Resurrect") is True:
                self.player.heal(20)
                self.player.set_property("Resurrect", False)
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.GAIN_HEALTH,
                                            description=f"You fall to the ground but a strange aura surrounds uou!"))
            else:
                self.current_floor.swap_entity(self.player, "Dead Player")
                self.state = Model.GAME_STATE_GAME_OVER
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.PLAYER_DEAD,
                                            description=f"You died!"))

                self.events.add_event(Event(type=Event.STATE,
                                            name=Event.STATE_GAME_OVER,
                                            description=f"Game Over!"))

    def set_state(self, new_state):
        """
        Change the stats of the model to a new state but store what the old state was
        :rtype: object
        :arg new_state the new state that you want so set the model to
        """
        if new_state != self.state:
            self._old_state = self.state
            self.state = new_state

            self.events.add_event(Event(type=Event.STATE,
                                        name=new_state,
                                        description=f"{self.name}: {new_state.upper()}"))

    def set_mode(self, new_mode):
        self.set_state(new_mode)

    def get_next_event(self)->Event:
        """
        Get the next event in the Model's event queue.

        :return:The next event in the event queue

        """
        next_event = None
        if self.events.size() > 0:
            next_event = self.events.pop_event()
        return next_event

    def generate_player(self, name:str, class_name:str)->Player:
        """
        Create an instance of a Player with the specified name, give them a combat class
        and give them some basic equipment.

        :param name: The name that you want to give to the new player
        :return: The newly created Player object
        """


        player_entity = EntityFactory.get_entity_by_name("Player")

        # Create a new player
        new_player = Player(name=name,
                            char=player_entity.char,
                            description=player_entity.description,
                            category=player_entity.category,
                            fg = player_entity.fg)

        new_player.properties = copy.deepcopy(player_entity.properties)

        # Assign them a combat class
        cc = CombatClassFactory.get_combat_class_by_name(class_name)
        new_player.fighter = Fighter(combat_class=cc)


        # Give the player their class equipment
        class_equipment = new_player.fighter.get_property("StartingEquipment").split(",")

        for item in class_equipment:
            eq = EntityFactory.get_entity_by_name(item.strip())
            new_player.take_item(eq)
            new_player.equip_item(eq)

        # Give the player their class items and some basic items
        class_items = new_player.fighter.get_property("StartingItems").split(",")
        base_items = ["Food", "Food", "Small Red Potion"]
        starting_items = class_items + base_items

        for item in starting_items:
            eq = EntityFactory.get_entity_by_name(item.strip())
            new_player.take_item(eq)

        # Give the Player some money
        coins = {Inventory.GOLD: 0, Inventory.SILVER:1, Inventory.COPPER:7}
        for c,v in coins.items():
            eq = EntityFactory.get_entity_by_name(c)
            for i in range(v):
                new_player.take_item(eq)

        new_player.level_up()

        return new_player

    def add_player(self, new_player: Player):
        self.player = new_player

        self.events.add_event(Event(type=Event.GAME,
                                    name=Event.GAME_NEW_PLAYER,
                                    description=f"{self.player.combat_class_name} {self.player.name} joined {self.name}!"))

        if self.current_floor is not None:
            self.current_floor.add_player(self.player)

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

            success = self.player.take_item(e)

            # If we manage to pick up an item then remove it from the floor
            if success is True:
                self.current_floor.swap_entity(e)
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.ACTION_TAKE_ITEM,
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

        # If we found up stairs go to the previous floor
        elif e.name == "Up Stairs":
            self.previous_floor()

        # If we found a shop then enter it
        elif e.name == "Shop":
            self.enter_shop()

        # Else the entity at this space is not stairs!
        else:
            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.ACTION_FAILED,
                                        description=f"There are no stairs here!"))

    def enter_shop(self):
        """
        Process entering a Shop
        """
        self.events.add_event(Event(type=Event.GAME,
                                    name=Event.GAME_ENTER_SHOP,
                                    description=f"You enter the shop!"))

        # Update the game parameters based on the current level
        game_parameters = self.load_game_parameters()

        # Create a new floor and initialise it
        # This will hold a random selection of items that can be sold in the shop
        shop_floor = Floor(f'The Shop on Level {self.dungeon_level}',
                                   50, 50,
                                   level=self.dungeon_level,
                                   params=game_parameters)

        shop_floor.initialise(self.events)

        # Add the new shop floor to the shop
        self.shop.initialise(shop_floor)


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
            """
            Process the Floor that the Player has just completed and move to tteh next floor
            """

            # Print the stats for the Floor that you just completed
            if self.current_floor is not None:


                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.GAME_FLOOR_COMPLETED,
                                            description=f"{self.current_floor.name} completed:"))

                # Report how well the Player did on this Floor
                stats = self.current_floor.get_stats()
                for stat in stats:
                    self.events.add_event(Event(type=Event.GAME,
                                                name=Event.GAME_FLOOR_COMPLETED,
                                                description=f"  * {stat}"))

                # Reward the player with some XP
                xp = self.current_floor.get_XP_reward()
                self.player.fighter.add_XP(self.current_floor.get_XP_reward())
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.ACTION_GAIN_XP,
                                            description=f"{xp} XP awarded"))

                # Heal the player
                self.player.heal(10)
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.ACTION_SUCCEEDED,
                                            description=f"You rest from your adventuring and heal your wounds"))

            # Increase the dungeon level
            self.dungeon_level += 1

            # Update the game parameters based on the new level
            game_parameters = self.load_game_parameters()

            # If the new level doesn't exist yet then create it...
            if self.dungeon_level > len(self.floors):

                # Create a new floor and initialise it
                floor_name = ThemeManager.get_random_history("Floor")
                self.current_floor = Floor(floor_name,
                                           50, 50,
                                           level=self.dungeon_level,
                                           params=game_parameters)

                self.current_floor.initialise(self.events)
                self.floors.append(self.current_floor)

            # Otherwise retrieve it
            else:
                self.current_floor = self.floors[self.dungeon_level-1]

            # Add the player at the start of the new level
            self.current_floor.add_player(self.player)
            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.GAME_NEW_FLOOR,
                                        description=f"{self.current_floor.theme}:{self.current_floor.name} on level {self.dungeon_level} ready!"))

            # Let the Player know if they can level up now!
            player_level = game_parameters["Game"]["Player"]["Level"]
            if player_level > self.player.get_property("Level"):
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.LEVEL_UP_AVAILABLE,
                                            description=f"*** Time to level up to level {player_level}! ***"))



    def equip_item(self, new_item : Entity)->bool:
        """
        Attempt to equip the specified item
        :param new_item: the new item that you want the Player to equip
        :return: True if we succeeded in equipping the item else False
        """
        success = False

        # If this item is an equippable item e.g. Sword, Shield....
        if new_item.get_property("IsEquippable") == True:

            # Attempt to equip it in the default slot for the item
            success = self.player.equip_item(new_item)
            if success is True:
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.ACTION_EQUIP,
                                            description=f"You equip {new_item.description}"))
            else:
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.ACTION_FAILED,
                                            description=f"You can't equip {new_item.description} right now"))

        # If this is a collectable item that you can use...
        elif new_item.get_property("IsCollectable") == True and new_item.get_property("IsInteractable") == True:

            # Attempt to equip it in the Item slot
            success = self.player.equip_item(new_item, Fighter.ITEM_SLOT)

            if success is True:
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.ACTION_EQUIP,
                                            description=f"You take {new_item.description} out of your backpack"))
            else:
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.ACTION_FAILED,
                                            description=f"You can't equip {new_item.description} right now"))
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

    def check_item(self, selected_item : Entity = None)->bool:
        """

        :param selected_item:
        :return:
        """
        success = False

        if selected_item is None:
            # First see if there is anything at the current location.  If not then fail.
            e = self.current_floor.get_entity_at_pos(self.player.xy)
            if e is None:
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.ACTION_FAILED,
                                            description=f"There is nothing here!"))

                return success
            else:
                selected_item = e


        # If the item is not checkable then fail
        if selected_item.get_property("IsCheckable") == False:
            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.ACTION_FAILED,
                                        description=f"{selected_item.description} is nothing of interest"))

        else:

            success = self.current_floor.run_ability_check(selected_item)


        return success

    def use_item(self, selected_item : Entity = None)->bool:
        """
        Attempt to use a specified item. Default is to use item in Item Slot
        :param selected_item:
        :return:
        """
        use_equipped_item = selected_item is None
        
        success = False

        # No item specified so get the current equipped item
        if use_equipped_item is True:
            selected_item = self.player.fighter.current_item


        # If we haven't got an item to use then fail
        if selected_item is None:
            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.ACTION_FAILED,
                                        description=f"You don't have an item equipped to use!"))

        # If the item is not interactable then fail
        elif selected_item.get_property("IsInteractable") == False:
            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.ACTION_FAILED,
                                        description=f"You can't use {selected_item.description}!"))

        # Try and use the item equipped...
        else:

            success, effect = self.item_user.process(selected_item, self.current_floor)

            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.ACTION_SUCCEEDED,
                                        description=f"You use {selected_item.description}"))

            if success is True:
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.ACTION_SUCCEEDED,
                                            description=f"{effect}"))
            else:
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.ACTION_FAILED,
                                            description=f"{effect}"))

        if success is True:
            if use_equipped_item is True:
                self.player.equip_item(None, slot=Fighter.ITEM_SLOT)
            self.player.drop_item(selected_item)

        return success


    def level_up(self, stat_name = None)->bool:

         # Update the game parameters and get the level that the player can upgrade to
        game_parameters = self.load_game_parameters()
        player_level = game_parameters["Game"]["Player"]["Level"]

        if player_level > self.player.get_property("Level"):
            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.LEVEL_UP,
                                        description=f"You levelled up!"))


            success = self.player.level_up(stat_name=stat_name)

        else:

            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.ACTION_FAILED,
                                        description=f"You don't have enough XP to level up!"))

            success = False

        return success


    def buy_item(self, new_item : Entity)->bool:
        success = self.player.inventory.buy_item(new_item)

        if success is False:
            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.ACTION_FAILED,
                                        description=f"You failed to buy {new_item.description}!"))

        else:
            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.ACTION_SUCCEEDED,
                                        description=f"You bought {new_item.description}"))
            
            self.shop.buy_item(new_item)


        return success

    def sell_item(self, old_item : Entity)->bool:
        success = self.player.inventory.sell_item(old_item)

        if success is False:
            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.ACTION_FAILED,
                                        description=f"You failed to sell {old_item.description}!"))

        else:
            self.player.fighter.unequip_item(old_item=old_item)
            self.shop.sell_item(old_item)

            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.ACTION_SUCCEEDED,
                                        description=f"You sold {old_item.description}"))

        return success

class ItemUser():
    def __init__(self):
        self.randomisations = {}
        self.random_entity_map = {}

    def initialise(self):

        # What HP does an Entity give you?
        self.HP_increase = {"Food": 5,
                            "Small Green Potion": 10,
                            "Small Red Potion": 15,
                            "Healing Scroll": 20,
                            "Small Purple Potion": -10,
                            "Healing Herbs" : 5,
                            "Red Mushroom" : 5,
                            "Blue Mushroom": -5}

        # What can you swap an entity for?
        self.entity_swaps = {"Locked Chest":("Silver", "Food", "Small Green Potion",
                                             "Helmet", "Weapon Upgrade", "Scroll of Resurrection"),
                             "Crate":("Food", "Food", "Copper"),
                             "Barrel":("Food", "Small Red Potion", "Copper", "Key")}

        # If you use an item what effect does it have on the item you used it on?
        self.item_swaps = {"Key":{"Locked Chest":self.entity_swaps["Locked Chest"]}}

    def add_randomiser_group(self, group_name, entities):
        """
        Add a group of items that you want to be randomised e.g. a group of potions
        :param group_name: name of teh group of items e.g. Potion
        :param entities: the list of entities that you want randomised using the randomise() method
        """
        if group_name not in self.randomisations:
            self.randomisations[group_name] = []
        self.randomisations[group_name] = entities

    def randomise(self):
        """
        Randomise items and their effects that have been loaded using add_randomiser_group()
        """
        # For each group of items that you want to randomise...
        for group, entities in self.randomisations.items():
            # Get the list of items
            a = list(entities)
            # Build a list of just their names
            a_names = [i.name for i in a]

            # Shuffle the list of items into a new list
            b = random.sample(a, len(a))

            # Zip the original item names to teh shuffled list
            c = zip(a_names,b)

            # Store the mapping
            self.random_entity_map.update(dict(c))

        print(f'\t{self.random_entity_map}')

    def process(self, item: Entity, floor: Floor) -> bool:
        """
        Use a specified item in the context of a specified floor
        :param item: the item that is being used
        :param floor: the floor that the item is being used on
        :return: True is you successfully used the item else False
        """

        # Get useful objects that we will need when using items
        player = floor.player
        item_at_tile = floor.get_entity_at_pos(player.xy)
        last_enemy = floor.last_enemy
        original_item = item

        # If the specified has been randomised then map it to the random item
        if item.name in self.random_entity_map.keys():
            item = self.random_entity_map[original_item.name]
            print(f'\t** Using {item.name} instead of {original_item.name}')

        success = True
        drop = True
        effect = None

        # See if the item being used provides a change in HP...
        if item.name in self.HP_increase:
            hp_change = self.HP_increase[item.name]
            player.heal(hp_change)
            if hp_change>0:
                effect = "You regain some HP"
            else:
                effect = "You loose some HP"

        # Placeholder
        elif item.name == "Small Blue Potion":
            effect = "It tastes good.  Buuuurrrrrrppp!"

        # Gain experience
        elif item.name == "Small Bubbling Potion":
            level = player.get_property("Level")
            effect = "The potion grants you increased experience!"
            XP_reward = random.randint(level*10,level*50)
            player.fighter.add_XP(XP_reward)

        # Reveal the whole Floor map!!!
        elif item.name == "Map":
            intelligence = player.get_property("INT")
            probability = int(100 * intelligence/50)
            if random.randint(1,100) < probability:
                floor.reveal_map()
                effect = "You read the map to learn the layout of this floor!"
            else:
                effect = "You can't read the map so you throw it away in frustration!"
                player.drop_item(item)
                success = False

        # Reveal where the exit is
        elif item.name == "Scroll of Secrets":
            floor.reveal_map(only_exit=True)
            effect = "You learn where the exit to the next floor is"

        # Teleport to the exit
        elif item.name == "Scroll of Teleportation":
            floor.move_player(floor.last_room.centerx,
                                   floor.last_room.centery,
                                   relative=False)
            effect = "You are teleported to the exit to the next floor"

        # Reveal the location of enemies.  Probability of success based on Player's Intelligence.
        elif item.name == "Scroll of Revelation":
            intelligence = player.get_property("INT")
            probability = int(100 * intelligence/50)
            floor.reveal_entities_by_property("IsEnemy", probability)
            effect = "You reveal the location of some enemies on this floor."

        # Reveal the location of items. Probability of success based on Player's Intelligence.
        elif item.name == "Scroll of Greed":
            intelligence = player.get_property("INT")
            probability = int(100 * intelligence/50)
            floor.reveal_entities_by_property("IsCollectable", probability)
            effect = "You reveal the location of some items on this floor"

        # Open locked chests.  Probability of success based on Player's Dexterity.
        elif item.name == "Scroll of XYZ":
            ename = "Locked Chest"
            dexterity = player.get_property("DEX")
            probability = int(100 * dexterity/50)
            floor.swap_entities_by_name(ename, self.entity_swaps[ename] , probability)
            effect = "You unlock some locked treasure chests"

        # Enable resurection upon dying
        elif item.name == "Scroll of Resurrection":
            effect = "You feel a strange aura surround you"
            player.set_property("Resurrect", True)

        # Attack an enemy
        elif item.category == "Combat":
            if player.fighter.last_target is not None:
                effect = f"You invoke {original_item.description}"
                ce = CombatEquipmentFactory.get_equipment_by_name(item.name)
                floor.attack_entity(player, last_enemy, weapon=ce)
            else:
                effect = f'No target for {item.description}'
                success = False

        # Is the item swappable?
        elif item.name in self.item_swaps:
            swaps = self.item_swaps[item.name]
            if item_at_tile is not None and item_at_tile.name in swaps:
                new_entity = EntityFactory.get_entity_by_name(random.choice(swaps[item_at_tile.name]))
                floor.swap_entity(item_at_tile, new_entity)
                if new_entity is not None:
                    effect = f'You use {item.description}' \
                             f' on {item_at_tile.description}' \
                             f' and reveal {new_entity.description}'
                else:
                    effect = f'You use {item.description}' \
                             f' on {item_at_tile.description}' \
                             f' and nothing happens'
            else:
                success=False
                effect=f"Can't use {item.description} right now"

        # Reveal where the exit is
        elif item.name == "Weapon Upgrade":
            
            cw = player.fighter.current_weapon

            upgraded_weapon_name = f'{cw.name}+1'

            e = EntityFactory.get_entity_by_name(upgraded_weapon_name)

            if e is not None:
                if player.take_item(e) is True and player.equip_item(e) is True:
                    effect = f"You upgraded your weapon to {e.description}"
                    player.drop_item(cw)
                else:
                    effect = "upgrade didn't work???"
                    success = False
            else:
                effect = f"You can't upgrade {cw.description}!"
                success = False

        # Is the item swappable?
        elif item.name in self.entity_swaps:
            new_entity = EntityFactory.get_entity_by_name(random.choice(self.entity_swaps[item.name]))
            floor.swap_entity(item, new_entity)
            effect = f'You break open {item.description}' \
                     f' and reveal {new_entity.description}'
        else:
            success = False
            effect = "Nothing happens"

        # If we successfully used the item then remove it from Player's Inventory
        if success is True and drop is True:
            pass
            #success = self.player.drop_item(self.item)

        return success, effect

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

        self.combat_class = None
        self.target_entity = None
        self.navigator = None
        self.failed_ticks = 0
        self.failed_ticks_limit = 10

    def __str__(self):

        text = f"{self.name}: Bot {self.bot_entity.name} at {self.bot_entity.xy}:"
        if self.combat_class is not None:
            text+= f'range:{self.sight_range} '
        if self.target_entity is not None:
            text += f'target:{self.target_entity.name}'

        return text

    def set_instructions(self, new_target: Entity):
        self.target_entity = new_target
        self.combat_class = CombatClassFactory.get_combat_class_by_name(self.bot_entity.name)
        self.sight_range = self.combat_class.get_property("SightRange")

    def tick(self):
        """
        Tick this Bot
        :return:
        """
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

        # See if we are close enough to the target given the target's DEX abilities and
        # Check that there is a direct path to it i.e. bot is in current FOV
        d = self.distance_to_target(self.target_entity)
        target_dex_modifier = self.target_entity.fighter.get_property_modifier("DEX")
        target_in_range = d <= max(4,self.sight_range - target_dex_modifier)
        target_in_sight = self.bot_entity.xy in self.floor.get_fov_cells()

        # If we can attack it....
        attack_range = self.bot_entity.fighter.current_weapon_details.get_property("Range")
        if d <= attack_range:
            print(f'{self.bot_entity.name}: "I can attack you {self.target_entity.name} as range {d}<={attack_range}"')
            self.floor.attack_entity(self.bot_entity, self.target_entity)

        # if we can see it move closer...
        if target_in_range and target_in_sight:

            bx, by = self.bot_entity.xy
            tx, ty = self.target_entity.xy

            # Try and track the target's X position
            if tx != bx:
                if tx < bx:
                    self.floor.move_entity(self.bot_entity, -1,0, include_player=True)
                elif tx > bx:
                    self.floor.move_entity(self.bot_entity, 1, 0, include_player=True)

            # Try and track the target's Y position
            if ty != by:
                if ty < by:
                    self.floor.move_entity(self.bot_entity, 0, -1, include_player=True)
                elif ty > by:
                    self.floor.move_entity(self.bot_entity, 0, 1, include_player=True)

            # If we moved and are still in sight of the target then all good
            success = (bx,by) != self.bot_entity.xy or target_in_range

            print(f'{self.bot_entity.name}: "I can see you {self.target_entity.name} at d={d} with my range={self.sight_range} and your dex={target_dex_modifier}"')


        if self._debug is True and self.failed_ticks >0:
            print("Failed {0} vs. limit {1}".format(self.failed_ticks, self.failed_ticks_limit   ))

        return success

    def reset(self):
        super().reset()
        self.failed_ticks = 0


class AbilityCheck:
    difficulty_levels = {"Very easy": 5,
                         "Easy": 10,
                         "Medium": 15,
                         "Hard": 20,
                         "Very hard": 25,
                         "Nearly impossible": 30}

    ability_to_description = {
        "STR": "strength",
        "DEX": "dexterity",
        "INT": "intelligence",
        "CON": "constitution",
        "CHA": "charisma",
        "WIS": "wisdom"
    }

    def __init__(self,
                 entity: Entity,
                 ability: str,
                 difficulty: str,
                 description: str,
                 success_msg: str,
                 failure_msg: str,
                 max_attempts:int=-1):

        self.entity = entity
        self.ability = ability
        self.ability_name = AbilityCheck.ability_to_description[self.ability]
        self.difficulty = difficulty
        self.description = None if description == "" else description.format(entity=entity.description, ability=self.ability_name)
        self.success_msg = success_msg.format(entity=entity.description, ability=self.ability_name)
        self.failure_msg = failure_msg.format(entity=entity.description, ability=self.ability_name)
        self.max_attempts = max_attempts
        self.attempts_remaining = self.max_attempts

        if self.difficulty in AbilityCheck.difficulty_levels:
            self.difficulty_value = AbilityCheck.difficulty_levels[self.difficulty]
        else:
            self.difficulty_value = 0

        self.success_rewards = []
        self.failure_rewards = []
        self.success_stats = {}
        self.failure_stats = {}

        self.success_misc = {}
        self.failure_misc = {}

    def __str__(self):
        txt = f'{self.difficulty.upper()}:{self.difficulty_value} Check: {self.entity.name} versus {self.ability} ability - {len(self.success_rewards)} rewards:'
        for reward in self.success_rewards:
            txt += f'{reward},'

        return txt

    def add_reward(self, new_reward: str, success:bool = True):

        if success is True:
            self.success_rewards.append(new_reward)
        else:
            self.failure_rewards.append(new_reward)

    def add_reward_stat(self, new_stat:str, stats_reward_value:int, success:bool = True):
        if success is True:
            self.success_stats[new_stat] = stats_reward_value
        else:
            self.failure_stats[new_stat] = stats_reward_value


    def attempt(self, ability_modifier: int = 0):
        self.attempts_remaining -= 1
        self.success_reward = None
        self.failure_reward = None

        if self.difficulty_value <= (random.randint(1, 20) + ability_modifier):
            success = True
            if len(self.success_rewards) > 0:
                reward_name = random.choice(self.success_rewards)
                self.success_reward = EntityFactory.get_entity_by_name(reward_name)

        else:
            success = False
            if len(self.failure_rewards) > 0:
                reward_name = random.choice(self.failure_rewards)
                self.failure_reward = EntityFactory.get_entity_by_name(reward_name)

        return success


class AbilityChecksFactory:
    ability_checks = None

    def __init__(self):
        pass

    @staticmethod
    def load(file_name: str):

        # Create path for the file that we are going to load
        data_folder = Path(__file__).resolve().parent
        file_to_open = data_folder / "data" / file_name

        # Read in the csv file
        AbilityChecksFactory.ability_checks = pd.read_csv(file_to_open,encoding='latin1')
        df = AbilityChecksFactory.ability_checks
        df.set_index(["Entity", "Ability"], drop=True, inplace=True)
        df.fillna("", inplace=True)

        print(df.head())
        print(df.dtypes)

    @staticmethod
    def get_ability_check(entity_name: str, ability_name: str):

        assert AbilityChecksFactory.ability_checks is not None

        new_check = None

        df = AbilityChecksFactory.ability_checks

        check = df.loc[(entity_name, ability_name)]

        if check is not None:
            new_check = AbilityChecksFactory.ability_check_from_row(entity_name=entity_name,
                                                                    ability_name=ability_name,
                                                                    check=check)

        return new_check


    @staticmethod
    def ability_check_from_row(entity_name:str, ability_name:str, check)->AbilityCheck:

        difficulty = check["Difficulty"]
        description = check["Description"]
        success_msg = check["SuccessMsg"]
        failure_msg = check["FailureMsg"]
        success_rewards = check["SuccessRewards"]
        failure_rewards = check["FailureRewards"]
        success_stats = check["SuccessStats"]
        failure_stats = check["FailureStats"]
        max_attempts = check["MaxAttempts"]

        entity = EntityFactory.get_entity_by_name(entity_name)

        new_check = AbilityCheck(entity=entity,
                                 ability=ability_name,
                                 difficulty=difficulty,
                                 max_attempts=max_attempts,
                                 description=description,
                                 success_msg=success_msg,
                                 failure_msg=failure_msg)

        if success_rewards != "":
            for reward in success_rewards.split(','):
                new_check.add_reward(reward.strip(), success=True)

        if failure_rewards != "":
            for reward in failure_rewards.split(','):
                new_check.add_reward(reward.strip(), success=False)

        if success_stats != "":
            for reward in success_stats.split(','):
                stat, value = reward.split('=')

                if stat[0] == "#":
                    new_check.success_misc[stat[1:]] = value
                else:
                    new_check.add_reward_stat(stat, int(value), success=True)

        if failure_stats != "":
            for reward in failure_stats.split(','):
                stat, value = reward.split('=')

                if stat[0] == "#":
                    new_check.failure_misc[stat[1:]] = value
                else:
                    new_check.add_reward_stat(stat, int(value), success=False)

        return new_check


    def get_entity_ability_checks(entity_name: str):

        assert AbilityChecksFactory.ability_checks is not None, "No ability checks have been loaded!"

        matches = {}

        df = AbilityChecksFactory.ability_checks

        checks = df.loc[entity_name]

        for index, check in checks.iterrows():
            new_check = AbilityChecksFactory.ability_check_from_row(entity_name=entity_name,
                                                                    ability_name=index,
                                                                    check=check)
            matches[index] = new_check

        return matches
