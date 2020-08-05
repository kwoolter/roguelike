import collections

import numpy as np
import pygame.rect as rect
import tcod as libtcod

from .combat import *
from .entity_factory import Entity, Player, EntityFactory, Fighter
from .entity_factory import text_to_color
from .events import Event
from .game_parameters import GameParameters


def dim_rgb(rgb, dc: int):
    """
    Dim a colour by a specified amount
    :param rgb: the RGB colour that you want to dim
    :param dc: how much do you want to dim it by?
    :return: a libtcod.Color object with the dimmed RGB colour
    """
    r, g, b = rgb
    r = max(0, r - dc)
    g = max(0, g - dc)
    b = max(0, b - dc)
    return libtcod.Color(r, g, b)


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
        print(f'Room {self.name} located at {self.rect}')


class Floor():

    ROOM_COLOURS = ["darker_yellow",
                    "desaturated_amber",
                    "desaturated_orange",
                    "desaturated_flame",
                    "desaturated_lime",
                    "desaturated_chartreuse",
                    "grey",
                    "sepia_light"]

    ROOM_NAMES = ("The Guard Room", "The Store", "A Stone Chamber", "The Armoury", "Sleeping Quarters",
                  "The Crypt", "The Kitchen", "Torture Room", "The Wizard's Laboratory", "The Ossary",
                  "The Wine Cellar", "Food Store" , "Dank Cell")

    def __init__(self, name: str, width: int = 50, height: int = 50, level: int = 0, params = None):

        # Properties of this floor
        self.name = name
        self.width = width
        self.height = height
        self.level = level
        self.rect = rect.Rect(0, 0, width, height)

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
        floor_entities = []
        enames = self.floor_parameters.keys()
        for ename in enames:
            emax = self.floor_parameters[ename]['Count']
            eprob = self.floor_parameters[ename]['Probability']
            if emax>0 and eprob>0:
                floor_entities.append((ename,eprob,emax))

        print("*"*40)
        print(floor_entities)

        # List of floor tile colours that can be randomly assigned to a Room
        valid_room_colours = []
        for c in Floor.ROOM_COLOURS:
            lc = text_to_color(c)
            if lc is not None:
                # Make the colour even darker!
                lc = dim_rgb(list(lc), 35)
                valid_room_colours.append(lc)

        # List of floor tile colours that can be randomly assigned to a Tunnel
        valid_tunnel_colours = []
        for i in range(80,100,5):
            #valid_tunnel_colours.append(libtcod.Color(i,i,0))
            valid_tunnel_colours.append(libtcod.Color(i,i,i))

        print(valid_room_colours)

        # Define initial values for teh first and last room
        self.last_room = None
        self.first_room = None
        self.last_enemy=None

        for i in range(self.room_count):

            # Create a new room of random name, size and tile colour
            random_colour = random.choice(valid_room_colours)
            new_room = Room(name=random.choice(Floor.ROOM_NAMES),
                            w=random.randint(self.room_min_size, self.room_max_size),
                            h=random.randint(self.room_min_size, self.room_max_size),
                            bg=random_colour)

            # If we were able to add the room to the map...
            if self.add_map_room(new_room) is True:

                # if this is not the first room then...
                if self.last_room is not None:

                    # Add some random entities to the room using a template or count and probability
                    room_entities = room_entities_template.copy()
                    room_entities.append(("Pillar", 15, int(new_room.area / 10)))
                    self.add_entities_to_room(new_room, entities=room_entities)

                    # Create a tunnel connecting back to the previous room
                    random_tunnel_colour = random.choice(valid_tunnel_colours)
                    new_tunnel = Tunnel(start_pos=self.last_room.center,
                                        end_pos=new_room.center,
                                        bg=random_tunnel_colour)
                    self.map_tunnels.append(new_tunnel)

                # Make the new room the last room
                self.last_room = new_room

            else:
                print('\t**Couldnt add room so skipping and moving on')

        # redefine first and last rooms
        self.last_room = self.map_rooms[-1]
        self.first_room = self.map_rooms[0]
        self.last_room.name = "Exit to next floor"
        self.first_room.name = "The Entrance"

        # Add random entities to the whole floor
        self.add_entities_to_floor(entities = floor_entities)

        # Build a map of the floor
        self.build_floor_map()

        self.entities_added = len(self.entities)


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
        Add random Fighter characteristics to an Entity
        :param new_entity: the entity that we want to turn into a Fighter
        """

        class_name = new_entity.name
        equipment = random.choices(("Hands", "Dagger", "Spear"), weights =[5,4,3], k=2)[0]

        cc = CombatClassFactory.get_combat_class_by_name(class_name)
        eq = EntityFactory.get_entity_by_name(equipment)

        new_fighter = Fighter(combat_class=cc)
        #new_fighter.level_up()
        #new_fighter.equip_item(eq)

        for i in range(1,self.level):
            if i % 3 == 0:
                pass
                #new_fighter.level_up()

        new_entity.fighter = new_fighter

    def add_entities_to_floor(self, entities: dict):

        # Add the player
        if self.player is not None:
            self.add_player(self.player)

        # Get list of all rooms on this floor but exclude the first and last rooms
        available_rooms = self.map_rooms[1:-1]

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

            # Recalculate their current FOV
            self.recompute_fov()

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

                # Else raise event about what entity is blocking you
                else:
                    self.events.add_event(
                        Event(type=Event.GAME,
                              name=Event.ACTION_FAILED,
                              description=f"{e.description} blocks your way!"))

            # Otherwise the way is block for another reason
            else:
                self.events.add_event(
                    Event(type=Event.GAME,
                          name=Event.ACTION_FAILED,
                          description=f"That way is blocked!"))

        return moved

    def move_entity(self, entity: Entity, dx: int, dy: int, relative:bool = True) -> bool:
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

        # If the destination is a valid path on the map...
        if self.walkable[entity.x + dx, entity.y + dy] > 0:

            # And no solid entity is blocking the way...
            e = self.get_entity_at_pos((entity.x + dx, entity.y+dy))
            if e is None or e.get_property("IsWalkable") == True:
                # Move the specified entity
                entity.move(dx, dy)

            # Something is blocking the way so fail
            else:
                success = False

        # Otherwise we can't walk to the new destination so fail
        else:
            success = False

        return success

    def get_entity_at_pos(self, pos : tuple)->Entity:
        """
        See if there is an Entity object occupying a specified xy position on the Floor
        :param pos: the xy position that you want to check
        :return: the Entity at the specified position if one was found otherwise None
        """
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
        """
        Swap an entity on the floor with a new entity
        :param old_entity: the entity that you want to swap out
        :param new_entity: the new entity that uyou want to replace it with. Default is None which means remove the old entity
        """
        if old_entity in self.entities:
            if new_entity is not None:
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

                # Roll some damage based on the attackers weapon and deduct damage from target's HP
                #dmg = CombatEquipmentFactory.get_damage_roll_by_name(weapon.name)
                dmg = weapon.get_damage_roll()

                target.fighter.take_damage(dmg)

                # Strip of the first word of the weapon description
                # e.g 'a small dagger' -> 'small dagger'
                weapon_name = weapon.description[weapon.description.find(' ')+1:]

                self.events.add_event(
                    Event(type=Event.GAME,
                          name=Event.ACTION_SUCCEEDED,
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
            for sx, sy in tunnel.get_segments():
                self.walkable[sx, sy] = 1
                self.floor_tile_colours[sx,sy] = list(tunnel.bg)

        # Make floor walkable where rooms are and store any floor tile colours
        for room in self.map_rooms:
            x, y, w, h = room.rect
            self.walkable[x:x + w, y: y + h] = 1
            self.floor_tile_colours[x:x + w, y: y + h] = list(room.bg)

        # Convert walkable to array of bools
        self.walkable = self.walkable > 0

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
        return ((px-ox)**2 + (py-oy)**2) * factor/ self.fov_radius2

    def get_revealed_entities(self):

        return self.revealed_entities


    def tick(self):

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
        self.floors=[]
        self.current_floor = None
        self.events = EventQueue()
        self.item_user = None

    def initialise(self):
        """
        Initialise an instance of the Model.

        """

        # Load game data from specified files
        GameParameters.load("game_parameters.csv")
        EntityFactory.load("entities.csv")
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


    def load_game_parameters(self)->dict:
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

    def tick(self):
        if self.state == Model.GAME_STATE_PLAYING:
            self.current_floor.tick()

        if self.player.fighter.is_dead == True:
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

        # Assign them a combat class
        cc = CombatClassFactory.get_combat_class_by_name(class_name)
        new_player.fighter = Fighter(combat_class=cc)

        # Give the player some basic equipment
        basic_equipment = ("Dagger", "Robe", "Sandals")
        for item in basic_equipment:
            eq = EntityFactory.get_entity_by_name(item)
            new_player.take_item(eq)
            new_player.fighter.equip_item(eq)

        # Give the player some basic items
        basic_items = ("Food", "Food", "Small Red Potion", "Key")
        for item in basic_items:
            eq = EntityFactory.get_entity_by_name(item)
            new_player.take_item(eq)
            
        new_player.level_up()

        return new_player

    def add_player(self, new_player: Player):
        self.player = new_player

        self.events.add_event(Event(type=Event.GAME,
                                    name=Event.GAME_NEW_PLAYER,
                                    description=f"{self.player.name} the {self.player.combat_class} joined {self.name}!"))

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
                self.current_floor = Floor(f'The Floor {self.dungeon_level}',
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
                                        description=f"{self.name}: Dungeon Level {self.dungeon_level} Ready!"))

            # Let the Player know if they can level up now!
            player_level = game_parameters["Game"]["Player"]["Level"]
            if player_level > self.player.get_property("Level"):
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.LEVEL_UP_AVAILABLE,
                                            description=f"*** Time to level up to level {player_level}! ***"))



    def equip_item(self, new_item : Entity)->bool:
        """
        Attempt to equipe the specified item
        :param new_item: the new item that you want the Player to equip
        :return: True if we succeeded in equipping the item else False
        """
        success = False

        if new_item.get_property("IsEquippable") == True:
            success = self.player.equip_item(new_item)
            if success is True:
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.ACTION_EQUIP,
                                            description=f"You equip {new_item.description}"))

        elif new_item.get_property("IsCollectable") == True and new_item.get_property("IsInteractable") == True:

            success = self.player.equip_item(new_item, Fighter.ITEM_SLOT)

            if success is True:
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.ACTION_EQUIP,
                                            description=f"You take {new_item.description} out of your backpack"))

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

    def use_item(self, new_item : Entity = None)->bool:
        """
        Attempt to use a specified item. Default is to use item in Item Slot
        :param new_item:
        :return:
        """
        use_equipped_item = new_item is None
        
        success = False

        # No item specified so get the current equipped item
        if use_equipped_item is True:
            new_item = self.player.fighter.current_item

        # If we haven't got an item to use then fail
        if new_item is None:
            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.ACTION_FAILED,
                                        description=f"You don't have an item equipped to use!"))

        # If we have an item that you can interact with...
        elif new_item.get_property("IsInteractable") == True:

            success, effect = self.item_user.process(new_item, self.current_floor)

            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.ACTION_SUCCEEDED,
                                        description=f"You use {new_item.description}"))

            if success is True:
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.ACTION_SUCCEEDED,
                                            description=f"{effect}"))
            else:
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.ACTION_FAILED,
                                            description=f"{effect}"))

        # Otherwise we can't use this item
        else:
            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.ACTION_FAILED,
                                        description=f"You can't use {new_item.description}"))

        if success is True:

            if use_equipped_item is True:
                self.player.equip_item(None, slot=Fighter.ITEM_SLOT)

            self.player.drop_item(new_item)

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


class ItemUser():
    def __init__(self):
        self.randomisations = {}
        self.random_entity_map = {}

    def initialise(self):


        self.HP_increase = {"Food": 5, "Small Green Potion": 10, "Small Red Potion": 15, "Healing Scroll": 20, "Small Purple Potion": -10}

        # What can you swap an entity for?
        self.entity_swaps = {"Locked Chest":("Gold", "Food", "Small Green Potion", "Helmet")}

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
                effect = f'You use {item.description}' \
                         f' on {item_at_tile.description}' \
                         f' and reveal {new_entity.description}'
            else:
                success=False
                effect=f"Can't use {item.description} right now"

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

        #if d < self.bot_entity.fighter.current_weapon_details.get_property("Range"):
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
