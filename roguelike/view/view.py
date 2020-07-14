import tcod as libtcod
import numpy as np
from roguelike import model
from .view_utils import TextEntryBox


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

        self.floor_view = FloorView(self.width, self.height)
        self.text_entry = TextEntryBox()

    def initialise(self, model: model.Model):

        self.game = model
        font_file_dir = ".\\roguelike\\view\\fonts\\"

        font_file_specs = {
            "dundalk12x12_gs_tc.png": libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD,
            "polyducks_12x12.png": libtcod.FONT_LAYOUT_ASCII_INROW,
            "terminal8x12_gs_ro.png": libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_ASCII_INROW
        }

        font_file = "polyducks_12x12.png"
        font_file = "dundalk12x12_gs_tc.png"
        # font_file = "terminal8x12_gs_ro.png"

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

        self.con.default_bg = libtcod.dark_grey
        libtcod.console_clear(self.con)

        libtcod.console_set_char_background(self.con, 0, 0, libtcod.red)

        x = 30
        y = 30

        box2 = ([178, 178, 178, 178, 178],
                [178, 32, 32, 32, 178],
                [178, 32, 32, 32, 178],
                [178, 32, 32, 32, 178],
                [178, 178, 178, 178, 178])

        self.con.default_fg = libtcod.white
        self.con.default_bg = libtcod.red
        for i, r in enumerate(box2):
            for ii, c in enumerate(r):
                if c == 32:
                    continue
                libtcod.console_put_char(self.con, x + ii, y + i, chr(int(c)), libtcod.BKGND_OVERLAY)

        self.con.default_fg = libtcod.dark_green
        self.con.default_bg = libtcod.white
        self.con.print_(10, 46, "New Test", libtcod.BKGND_OVERLAY)
        libtcod.console_set_char_foreground(self.con, 10, 46, libtcod.black)

        player_x, player_y = self.game.player.xy

        self.con.default_fg = libtcod.lighter_blue
        libtcod.console_put_char(self.con, player_x, player_y, '@')
        libtcod.console_put_char(self.con, player_x, player_y + 1, chr(197))

        self.floor_view.draw()

        # libtcod.console_blit(self.floor_view.con, 0, 0, self.width, self.height, self.con, 0, 0, ffade=0.5, bfade=0.5)
        libtcod.console_blit(self.con, 0, 0, self.width, self.height, 0, 0, 0, ffade=0.5, bfade=0.5)

        # libtcod.console_credits_render(30,30,1)

        libtcod.console_flush()
        libtcod.console_put_char(self.con, player_x, player_y, ' ', libtcod.BKGND_NONE)
        libtcod.console_put_char(self.con, player_x, player_y + 1, ' ', libtcod.BKGND_NONE)

        # libtcod.console_set_default_background(self.con, libtcod.white)

    def do_text_entry(self):
        text_entry_box = TextEntryBox(width=20, height=3, parent = self.con, xpos=10, ypos=10)
        text_entry_box.fg = libtcod.red
        text_entry_box.bg = libtcod.white
        #text_entry_box.mask_ranges = [('0','9')]

        return text_entry_box.get_text(20)

class FloorView(View):
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.floor = None

    def initialise(self, floor: model.Floor):
        self.floor = floor
        self.con = libtcod.console_new(self.width, self.height)

    def draw(self):

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

        libtcod.console_set_default_foreground(self.con, libtcod.dark_green)
        libtcod.console_set_default_background(self.con, libtcod.green)

        x = 10
        y = 10

        box = ([218, 196, 194, 196, 191],
               [179, 32, 179, 32, 179],
               [195, 196, 197, 196, 180],
               [179, 32, 179, 32, 179],
               [192, 196, 193, 196, 217])

        for i, r in enumerate(box):
            for ii, c in enumerate(r):
                libtcod.console_print(self.con, x + ii, y + i, chr(int(c)))

        x = 30
        y = 10

        box2 = ([201, 205, 203, 205, 187],
                [186, 32, 186, 32, 186],
                [204, 205, 206, 205, 185],
                [186, 32, 186, 32, 186],
                [200, 205, 202, 205, 188])

        for i, r in enumerate(box2):
            for ii, c in enumerate(r):
                libtcod.console_print(self.con, x + ii, y + i, chr(int(c)))

        box3 = np.zeros((5, 5))
        box3.fill(int(178))

        x = 10
        y = 30

        for i, r in enumerate(box3):
            for ii, c in enumerate(r):
                libtcod.console_print(self.con, x + ii, y + i, chr(int(c)))

        box3 = np.zeros((5, 5))
        box3.fill(int(177))

        x = 15
        y = 10

        for i, r in enumerate(box3):
            for ii, c in enumerate(r):
                libtcod.console_print(self.con, x + ii, y + i, chr(int(c)))

        box3 = np.zeros((5, 5))
        box3.fill(int(176))

        x = 10
        y = 15

        for i, r in enumerate(box3):
            for ii, c in enumerate(r):
                libtcod.console_print(self.con, x + ii, y + i, chr(int(c)))

        x = 30
        y = 30

        box2 = ([178, 178, 178, 178, 178],
                [178, 32, 32, 32, 178],
                [178, 32, 32, 32, 178],
                [178, 32, 32, 32, 178],
                [178, 178, 178, 178, 178])

        for i, r in enumerate(box2):
            for ii, c in enumerate(r):
                if c == 32:
                    continue
                libtcod.console_print(self.con, x + ii, y + i, chr(int(c)))

        x = 50
        y = 50

        box2 = ([201, 205, 203, 205, 187],
                [186, 224, 186, 224, 186],
                [204, 205, 206, 205, 185],
                [186, 225, 186, 225, 186],
                [200, 205, 202, 205, 188])

        for i, r in enumerate(box2):
            for ii, c in enumerate(r):
                libtcod.console_print(self.con, x + ii, y + i, chr(int(c)))

        x = 40
        y = 40

        arrows = ([32, 30, 32],
                  [17, 18, 16],
                  [32, 31, 32])

        for i, r in enumerate(arrows):
            for ii, c in enumerate(r):
                libtcod.console_print(self.con, x + ii, y + i, chr(int(c)))

        blocks = ([229, 228, 226],
                  [231, 230.230],
                  [229, 32, 232])

        x = 40
        y = 25
        libtcod.console_set_default_background(self.con, (255, 0, 0))

        for i, r in enumerate(blocks):
            for ii, c in enumerate(r):
                libtcod.console_put_char(self.con, x + ii, y + i, chr(int(c)))

        libtcod.console_set_default_background(self.con, libtcod.white)
        libtcod.console_print(self.con, 10, 40, "Hello World")
        self.con.print_(10, 45, "Test", bg_blend=libtcod.BKGND_ADD)


