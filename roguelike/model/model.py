import numpy as np

class Entity():
    def __init__(self, name:str, x:int, y:int):
        self.name = name
        self.x = x
        self.y = y

    @property
    def xy(self):
        return(self.x, self.y)

class Player(Entity):
    def __init__(self, name: str, x:int = 1, y:int = 1):
        super().__init__(name,x,y)

class Floor():
    def __init__(self, name:str, width:int = 80, height:int = 50):
        self.name = name
        self.width = width
        self.height = height
        self.player = None

        self.map = np.array(dtype = int)

    def add_player(self, new_player : Player, x:int = None, y:int = None):
        self.player = new_player

class Model():
    def __init__(self, name:str):
        self.name = name
        self.player = None

    def initialise(self):
        self.add_player(Player(name="Keith"))

    def tick(self):
        pass

    def add_player(self, new_player:Player):
        self.player = new_player

    def get_current_player(self):
        return self.player

    def move_player(self, dx:int, dy:int):
        self.player.x += dx
        self.player.y += dy
