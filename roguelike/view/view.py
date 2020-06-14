from roguelike import model
import tcod as libtcod

class View():
    def __init__(self):
        self.tick_count = 0

    def tick(self):
        self.tick_count += 0

    def draw(self):
        pass

class MainFrame():

    def __init__(self, width: int = 80, height:int = 50):
        super().__init__()
        self.width = width
        self.height = height
        self.game = None
        self.con = None

        self.floor_view = FloorView(self.width, self.height)

    def initialise(self, model: model.Model):

        self.game = model

        libtcod.console_set_custom_font('arial10x10.png',
                                        libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)

        libtcod.console_init_root(self.width,
                                  self.height,
                                  self.game.name,
                                  fullscreen=False)

        self.con = libtcod.console_new(self.width, self.height)

        self.floor_view.initialise(self.game.current_floor)

    def draw(self):
        player_x, player_y = self.game.player.xy

        libtcod.console_set_default_foreground(self.con, libtcod.white)
        libtcod.console_put_char(self.con, player_x, player_y, '@', libtcod.BKGND_NONE)

        self.floor_view.draw()
        libtcod.console_blit(self.floor_view.con, 0, 0, self.width, self.height, 0, 0, 0, ffade=0.7)
        libtcod.console_blit(self.con, 0, 0, self.width, self.height, 0, 0, 0, ffade=0.7, bfade=0.5)

        libtcod.console_flush()
        libtcod.console_put_char(self.con, player_x, player_y, ' ', libtcod.BKGND_NONE)

class FloorView(View):
    def __init__(self, width:int, height:int):
        self.width = width
        self.height = height
        self.floor = None
        
    def initialise(self, floor:model.Floor):
        self.floor = floor
        self.con = libtcod.console_new(self.width, self.height)
        
    def draw(self):

        for e in self.floor.entities:
            x,y = e.xy
            libtcod.console_set_default_foreground(self.con, libtcod.yellow)
            libtcod.console_put_char(self.con, x, y, '@', libtcod.BKGND_NONE)


        