import numpy as np

from roguelike import model
from .view_utils import *


class View():
    def __init__(self):
        self.tick_count = 0

    def tick(self):
        self.tick_count += 0

    def draw(self):
        pass


class MainFrame():

    def __init__(self, width: int = 80, height: int = 50):
        super().__init__()
        self.width = width
        self.height = height
        self.game = None
        self.con = None

        self.floor_view = FloorView(self.width, self.height, bg=libtcod.darkest_grey)
        self.text_entry = TextEntryBox()

    def initialise(self, model: model.Model):

        self.game = model
        font_file_dir = ".\\roguelike\\view\\fonts\\"

        font_file_specs = {
            "dejavu_wide16x16_gs_tc.png": libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD,
            "dundalk12x12_gs_tc.png": libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD,
            "polyducks_12x12.png": libtcod.FONT_LAYOUT_ASCII_INROW,
            "terminal8x12_gs_ro.png": libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_ASCII_INROW
        }

        font_file = "polyducks_12x12.png"
        font_file = "dejavu_wide16x16_gs_tc.png"
        #font_file = "dundalk12x12_gs_tc.png"
        #font_file = "terminal8x12_gs_ro.png"

        libtcod.console_set_custom_font(font_file_dir + font_file,
                                        font_file_specs[font_file]
                                        )

        libtcod.console_init_root(self.width,
                                  self.height,
                                  self.game.name,
                                  fullscreen=False)

        self.con = libtcod.console_new(self.width, self.height)

        self.floor_view.initialise(self.game.current_floor)

    def draw(self):

        self.con.default_bg = libtcod.black
        libtcod.console_clear(self.con)

        self.floor_view.draw()

        libtcod.console_blit(self.floor_view.con, 0, 0, self.width, self.height, 0, 0, 0, ffade=1, bfade=1)

        libtcod.console_flush()


    def do_text_entry(self):
        text_entry_box = TextEntryBox(width=20, height=3, parent = self.con, xpos=10, ypos=10)
        text_entry_box.fg = libtcod.red
        text_entry_box.bg = libtcod.white
        #text_entry_box.mask_ranges = [('0','9')]

        return text_entry_box.get_text(20)

class FloorView(View):
    def __init__(self, width: int, height: int, fg = libtcod.white, bg=libtcod.grey):
        self.width = width
        self.height = height
        self.fg = fg
        self.bg = bg
        self.bg_explored = libtcod.dark_gray
        self.bg_fov = libtcod.darker_yellow

        self.floor = None

    def initialise(self, floor: model.Floor):
        self.floor = floor
        self.con = libtcod.console_new(self.width, self.height)

    def draw(self):

        # Clear the screen with the background colour
        self.con.default_bg = self.bg
        libtcod.console_clear(self.con)

        # Draw the walkable areas that we have already explored
        for x in range(self.floor.width):
            for y in range(self.floor.height):

                if self.floor.fov_map[x,y] == True:
                    libtcod.console_set_char_background(self.con, x, y, self.bg_fov)

                elif self.floor.map[x,y] > 0 and self.floor.explored[x,y] == True:
                    libtcod.console_set_char_background(self.con, x, y, self.bg_explored)


        # Draw the player
        so = ScreenObject('@', fg=libtcod.black, bg=self.bg_fov)
        so.render(self.con, x=self.floor.player.x, y=self.floor.player.y)


    def draw_old(self):

        for e in self.floor.entities:
            x, y = e.xy
            libtcod.console_set_default_foreground(self.con, libtcod.yellow)
            libtcod.console_put_char(self.con, x, y, chr(130), libtcod.BKGND_NONE)

        for c in range(0, 255):
            x = c % 50
            y = c // 50
            libtcod.console_put_char(self.con, x, y, chr(c), libtcod.BKGND_NONE)

        y = 5
        for c in range(200, 255):
            libtcod.console_print(self.con, 0, y, f'{c}:{chr(c)}')

            y += 1

        box = ([218, 196, 194, 196, 191],
               [179, 32, 179, 32, 179],
               [195, 196, 197, 196, 180],
               [179, 32, 179, 32, 179],
               [192, 196, 193, 196, 217])
        x=5
        y=5
        so = ScreenObject2DArray(box, fg=libtcod.dark_sea, bg=libtcod.grey)
        so.render(self.con, x,y)

        x += 10

        box2 = ([201, 205, 203, 205, 187],
                [186, 32, 186, 32, 186],
                [204, 205, 206, 205, 185],
                [186, 32, 186, 32, 186],
                [200, 205, 202, 205, 188])
        so = ScreenObject2DArray(box2, fg=libtcod.dark_sea, bg=libtcod.grey)
        so.render(self.con, x,y)

        x += 10

        box3 = np.zeros((5, 5))
        box3.fill(int(178))

        so = ScreenObject2DArray(box3, fg=libtcod.dark_sea, bg=libtcod.grey)
        so.render(self.con, x,y)

        x += 10

        box3 = np.zeros((5, 5))
        box3.fill(int(177))

        so = ScreenObject2DArray(box3, fg=libtcod.dark_sea, bg=libtcod.grey)
        so.render(self.con, x,y)

        x += 10
        box3 = np.zeros((5, 5))
        box3.fill(int(176))
        so = ScreenObject2DArray(box3, fg=libtcod.dark_sea, bg=libtcod.grey)
        so.render(self.con, x,y)

        x = 5
        y += 10

        box2 = ([178, 178, 178, 178, 178],
                [178, 32, 32, 32, 178],
                [178, 32, 32, 32, 178],
                [178, 32, 32, 32, 178],
                [178, 178, 178, 178, 178])

        so = ScreenObject2DArray(box2, fg=libtcod.dark_sea, bg=libtcod.grey)
        so.render(self.con, x,y)

        x += 10

        box2 = ([201, 205, 203, 205, 187],
                [186, 224, 186, 224, 186],
                [204, 205, 206, 205, 185],
                [186, 225, 186, 225, 186],
                [200, 205, 202, 205, 188])

        so = ScreenObject2DArray(box2, fg=libtcod.dark_sea, bg=libtcod.grey)
        so.render(self.con, x,y)

        x += 10

        arrows = ([32, 30, 32],
                  [17, 18, 16],
                  [32, 31, 32])

        so = ScreenObject2DArray(arrows, fg=libtcod.dark_sea, bg=libtcod.grey)
        so.render(self.con, x,y)

        x += 10

        blocks = ([229, 32, 228, 32, 232],
                  [32,32,32,32,32],
                  [231, 32, 230, 32, 230],
                  [32, 32, 32, 32, 32],
                  [231, 32, 228,32, 226])

        so = ScreenObject2DArray(blocks, fg=libtcod.dark_sea, bg=libtcod.grey)
        so.render(self.con, x,y)

        libtcod.console_set_default_background(self.con, libtcod.white)
        libtcod.console_print(self.con, 10, 40, "Hello World")
        self.con.print_(10, 45, "Test", bg_blend=libtcod.BKGND_ADD)

        o = ScreenObject("K", fg=libtcod.red, bg=libtcod.yellow)
        o.render(self.con,17,17)

        s = ScreenString("Hello World", fg = libtcod.red, bg=libtcod.white)
        s.render(self.con, 10,10)
        s.render(self.con, 10,12, alignment=libtcod.CENTER)

        bo = ScreenObject2DArray(box2, fg=libtcod.orange, bg=libtcod.yellow)
        bo.render(self.con, 40,10)

        text_box = ['###','#O#','###']
        bo = ScreenObject2DArray(text_box, fg=libtcod.red, bg=libtcod.white)
        bo.render(self.con, 40,20)

        s = "This is the end. My only friend, the end. I'll never look into your eyes again!"
        sr = ScreenStringRect(text=s, width=10, height=10,
                              fg=libtcod.darkest_blue, bg=libtcod.lightest_lime,
                              alignment=libtcod.CENTER)
        sr.render(self.con, 20,20)

        libtcod.console_set_default_background(self.con, self.bg)
        libtcod.console_clear(self.con)

        for room in self.floor.map_rooms.values():
            box = np.array([['#' for y in range(room.height+2)] for x in range(room.width+2)])
            box[1:-1,1:-1] = ScreenObject.BLANK_CHAR
            bo = ScreenObject2DArray(box, fg=room.fg, bg=room.bg)
            bo.render(self.con, room.x-1, room.y-1)

            # s = ScreenString(room.name, fg = libtcod.red, bg=libtcod.white)
            # s.render(self.con, room.x-1,room.y-2, alignment=libtcod.LEFT)

        for tunnel in self.floor.map_tunnels:
            so = ScreenObjectList(char=ScreenObject.BLANK_CHAR,
                                  positions=tunnel.get_segments(),
                                  fg=tunnel.fg,
                                  bg=tunnel.bg)
            so.render(self.con)




