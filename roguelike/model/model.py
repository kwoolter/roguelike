import numpy as np
import random

class Entity():
    def __init__(self, name:str, x:int, y:int):
        self.name = name
        self.x = x
        self.y = y

    @property
    def xy(self):
        return(self.x, self.y)

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

class Floor():
    def __init__(self, name:str, width:int = 80, height:int = 50):
        self.name = name
        self.width = width
        self.height = height
        self.player = None
        self.entities = []

    def initialise(self):
        for i in range(10):
            self.entities.append(Entity(name="NPC",
                                        x=random.randint(1,self.width),
                                        y=random.randint(1,self.height)))

        # self.map = np.array(dtype = int)

    def add_player(self, new_player : Player, x:int = None, y:int = None):
        if x is None:
            x = int(self.width/2)
        if y is None:
            y = int(self.height/2)

        self.player = new_player
        self.player.xy = (x,y)


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

    def tick(self):
        pass

    def add_player(self, new_player:Player):
        self.player = new_player

    def get_current_player(self):
        return self.player

    def move_player(self, dx:int, dy:int):
        self.player.move(dx, dy)
