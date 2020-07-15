import random
import tcod as libtcod
import pygame.rect as rect
import random
import numpy as np

import pygame.rect as rect
import tcod as libtcod


class Entity():
    def __init__(self, name:str, x:int, y:int):
        self.name = name
        self.x = x
        self.y = y

    @property
    def xy(self):
        return self.x, self.y

    @xy.setter
    def xy(self, new_xy):
        x,y = new_xy
        self.x = x
        self.y = y

    def move(self, dx:int, dy:int):
        self.x += dx
        self.y += dy

class Player(Entity):
    def __init__(self, name: str, x:int = 1, y:int = 1):
        super().__init__(name,x,y)

class Tunnel:

    DIRECTION_V_H = "VH"
    DIRECTION_H_V = "HV"
    DIRECTIONS = (DIRECTION_V_H, DIRECTION_H_V)

    def __init__(self, start_pos, end_pos, direction = None, fg=libtcod.white, bg=libtcod.black):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.fg = fg
        self.bg=bg

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

        for x in range(min(start_x, end_x), max(start_x, end_x)+1):
            segments.append((x,hy))

        for y in range(min(start_y, end_y), max(start_y, end_y)+1):
            segments.append((vx,y))

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
        # other_room_walls = other_room.rect.inflate(2,2)
        # print(f'room r:{self.rect}, other room r:{other_room.rect}, other room walls r:{other_room_walls}')
        # print(f'colliding {self.rect.colliderect(other_room_walls)}')
        return self.rect.colliderect(other_room.rect.inflate(2,2)) > 0

    def print(self):
        print(f'Room {self.name} located at {self.rect}')

class Floor():
    def __init__(self, name:str, width:int = 80, height:int = 50):
        self.name = name
        self.width = width
        self.height = height
        self.rect = rect.Rect(0,0,width,height)
        self.player = None
        self.first_room = None
        self.room_count = 15
        self.map_rooms = {}
        self.map_tunnels = []
        self.entities = []

        self.map = None
        self.explored = None

        self.fov_map = None
        self.fov_radius = 5

    def initialise(self):

        self.map_rooms = {}
        self.map_tunnels = []
        self.fov_map = None

        for i in range(10):
            self.entities.append(Entity(name="NPC",
                                        x=random.randint(1,self.width),
                                        y=random.randint(1,self.height)))

        last_room = None
        self.first_room = None

        for i in range(self.room_count):
            new_room = Room(f'Room{i}', random.randint(3,6),random.randint(3,6))
            if self.add_map_room(new_room) is True:
                if last_room is not None:
                    new_tunnel = Tunnel(last_room.center, new_room.center)
                    self.map_tunnels.append(new_tunnel)
                else:
                    self.first_room = new_room
                last_room = new_room

        self.build_floor_map()

        if self.player is not None:
            self.add_player(self.player)

    def print(self):
        print(f'Floor {self.name}: ({self.width},{self.height})')
        for room in self.map_rooms.values():
            room.print()

        for tunnel in self.map_tunnels:
            tunnel.print()

    def add_player(self, new_player : Player, x:int = None, y:int = None):
        if x is None:
            x, y = self.first_room.center
        if y is None:
            x, y = x, self.first_room.center

        self.player = new_player
        self.player.xy = (x,y)
        self.recompute_fov()

    def move_player(self, dx, dy):
        if self.map[self.player.x + dx, self.player.y + dy] > 0:
            self.player.move(dx,dy)
            self.recompute_fov()

    def add_map_room(self, new_room:Room)->bool:
        """:param"""

        attempts = 10
        overlap = True

        # Shrink floor rect to allow for border
        floor_rect = self.rect.inflate(-2,-2)

        # Try a specified number of times to find a random space for the new room
        while overlap is True and attempts > 0:

            # Generate random centre
            cx = random.randint(floor_rect.left, floor_rect.right)
            cy = random.randint(floor_rect.top, floor_rect.bottom)
            new_room.rect.center = (cx,cy)

            # If the random room location fits within the floor boundaries...
            if floor_rect.contains(new_room.rect):
                overlap=False
                # Check to see if we arenot touching an existing room...
                for room in self.map_rooms.values():
                    if new_room.is_touching(room):
                        overlap = True
                        break

        # If we found a free space for the new room add it to the floor map
        if overlap is False:
            self.map_rooms[new_room.name] = new_room
            print(f'Added new room {new_room.name} at ({new_room.x},{new_room.y}) after {11-attempts} attempts')

        return not overlap

    def run_room_check(self):
        for room1 in self.map_rooms.values():
            for room2 in  self.map_rooms.values():
                if room1 is room2:
                    continue
                x = room1.is_touching(room2)

                print(f'room {room1.name} vs. room {room2.name}touching={x}')


    def build_floor_map(self):
        self.map = np.zeros((self.width, self.height))
        self.explored = np.zeros((self.width, self.height), dtype=bool)

        for room in self.map_rooms.values():
            x,y,w,h = room.rect
            self.map[x:x+w, y: y+h] = 1

        for tunnel in self.map_tunnels:
            for sx, sy in tunnel.get_segments():
                self.map[sx,sy] = 1

    def recompute_fov(self, x=None, y=None, radius=None, light_walls=False, algorithm=0):

        if x is None and self.player is not None:
            x = self.player.x

        if y is None and self.player is not None:
            y = self.player.y

        if radius is None:
            radius = self.fov_radius

        t = self.map > 0

        self.fov_map = libtcod.map.compute_fov(t,
                                               (x,y),
                                               radius,
                                               light_walls,
                                               algorithm)

        self.explored |= self.fov_map

        return self.fov_map


class Model():
    def __init__(self, name:str):
        self.name = name
        self.player = None
        self.current_floor = None

    def initialise(self):
        self.add_player(Player(name="Keith"))
        self.current_floor = Floor("Test", 50, 50)
        self.current_floor.initialise()
        self.current_floor.add_player(self.player)

    def print(self):
        self.current_floor.print()

    def tick(self):
        pass

    def add_player(self, new_player:Player):
        self.player = new_player

    def get_current_player(self):
        return self.player

    def move_player(self, dx:int, dy:int):
        self.current_floor.move_player(dx, dy)

    def new_floor(self):
        self.current_floor.initialise()
