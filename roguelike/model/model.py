import collections
import random

import numpy as np
import pygame.rect as rect
import tcod as libtcod

from .events import Event
from .entity_factory import Entity, Player, EntityFactory


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

        # Which parts of the floor are:-
        # - Walkable?
        # - Have already been explored?
        # - Are in the current FOV?
        self.walkable = None
        self.explored = None
        self.fov_map = None
        self.fov_radius = 5

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
            new_room = Room(f'Room{i}', random.randint(3, 6), random.randint(3, 6))

            # If we were able to add the room to the map...
            if self.add_map_room(new_room) is True:

                # Add some random entities to the room
                self.add_entities_to_room(new_room)

                # if this is not the first room then create a tunnel to teh previous room
                if last_room is not None:
                    new_tunnel = Tunnel(last_room.center, new_room.center)
                    self.map_tunnels.append(new_tunnel)
                else:
                    self.first_room = new_room

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

    def add_entities_to_room(self, room : Room):

        l = self.level

        entities = (("Gold", (1+ l//3)*5, 1), ("Orc", 30, 3), ("Troll", 5*(l//10), 1))
        for ename, eprob, emax in entities:
            for count in range(emax):
                if random.randint(1,100) < eprob:
                    rx,ry = room.get_random_pos()
                    if self.get_entity_at_pos((rx,ry)) is None:
                        new_entity = EntityFactory.get_entity_by_name(ename)
                        new_entity.xy = rx,ry
                        self.entities.append(new_entity)

    def add_entities_to_floor(self):

        # Add the player
        if self.player is not None:
            self.add_player(self.player)

        # Add stairs down to next level
        cx,cy= self.last_room.center
        self.entities.append(Entity(name='down stairs', char='v', x=cx, y=cy))

        # If we are not at the top level add stairs back up to the previous level
        if self.level > 1:
            cx,cy= self.first_room.center
            self.entities.append(Entity(name='up stairs', char='^', x=cx, y=cy))

        entities_to_add = [("NPC",3), ("Sword",2), ("Axe",2), ("Key",1), ("Fire Scroll",1), ("Healing Scroll",1)]

        # Add different stuff to random rooms
        for ename, ecount in entities_to_add:

            # Get list of all rooms on this floor but exclude the first and last rooms
            available_rooms = list(self.map_rooms.values())
            available_rooms.remove(self.first_room)
            available_rooms.remove(self.last_room)

            for i in range(ecount):

                # pick a random room
                room=random.choice(available_rooms)

                # Pick a random position in the room
                rx, ry = room.get_random_pos()

                # If there is nothing already there...
                if self.get_entity_at_pos((rx, ry)) is None:

                    # Add a new entity to the floor at this location
                    new_entity = EntityFactory.get_entity_by_name(ename)
                    if new_entity is None:
                        print(f"Couldn't create entity bny name of {ename}")
                        continue

                    new_entity.xy = rx,ry

                    self.entities.append(new_entity)

                    # Don't use this room again
                    available_rooms.remove(room)


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
                          description=f"You found {e.name}!"))

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
            self.events.add_event(
                Event(type=Event.GAME,
                      name=Event.ACTION_FAILED,
                      description=f"That way is blocked!"))

    def move_entity(self, entity: Entity, dx: int, dy: int) -> bool:

        success = True
        # If the destination is a valid path...
        if self.walkable[entity.x + dx, entity.y + dy] > 0:
            entity.move(dx, dy)
        else:
            success = False

        return success

    def get_entity_at_pos(self, pos : tuple)->Entity:
        for e in self.entities:
            if e.xy == pos:
                return e
        return None

    def swap_entity(self, old_entity : Entity, new_entity : Entity = None):
        if old_entity in self.entities:
            if new_entity is not None:
                new_entity.xy = old_entity.xy
                self.entities.append(new_entity)

            self.entities.remove(old_entity)
        else:
            print(f"Couldn't find {old_entity.name} on this floor!")


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


class Model():
    def __init__(self, name: str):
        # Properties of the game
        self.name = name
        self.dungeon_level = 0

        # Contents of the game
        self.player = None
        self.inventory = {}
        self.entities = None
        self.floors=[]
        self.current_floor = None
        self.events = EventQueue()

    def initialise(self):

        EntityFactory.load("entities.csv")

        self.add_player(Player(name="Keith"))
        self.next_floor()

    def print(self):
        self.current_floor.print()

    def tick(self):
        pass

    def get_next_event(self):
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

    def take_item(self):

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

            # If you don't have any of these set inventory count to 1
            if e.name not in self.inventory.keys() or self.inventory[e.name] == 0:
                self.inventory[e.name] = 1
                success = True

            # If the item is stackable then increase the number you are holding
            elif e.get_property("IsStackable") == True:
                self.inventory[e.name] += 1
                success = True

            # Otherwise you can't hold any more of these so fail
            else:
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.ACTION_FAILED,
                                            description=f"You can only hold one {e.name}!"))

            # If we manage to pick up an item then remove it
            if success is True:
                self.current_floor.swap_entity(e)
                self.events.add_event(Event(type=Event.GAME,
                                            name=Event.ACTION_SUCCEEDED,
                                            description=f"You picked up {e.name}!"))

        # Otherwise you can't pick it up
        else:
            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.ACTION_FAILED,
                                        description=f"You can't pick up {e.name}!"))

        print(self.inventory)

        if e is not None:
            print(e)
            print(e.properties)
            property_name = "IsCollectable"
            property_value = e.get_property(property_name)
            if property_value is True:
                print("is true")
            elif property_value == True:
                print("eq True")
            else:
                print("False")

    def take_stairs(self):

        # First see if there is anything at the current location.  If not then fail.
        e = self.current_floor.get_entity_at_pos(self.player.xy)
        if e is None:
            self.events.add_event(Event(type=Event.GAME,
                                        name=Event.ACTION_FAILED,
                                        description=f"There is nothing here!"))

        # If we found down stairs go to next floor
        elif e.name == "down stairs":
            self.next_floor()

        # If we found up stairs go to teh previous floor
        elif e.name == "up stairs":
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

