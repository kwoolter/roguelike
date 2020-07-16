import tcod as libtcod
import textwrap
import numpy as np

def text_to_color(color_text :str)->libtcod.color.Color:

    c = None

    try:
        c = eval(f'libtcod.{color_text.lower()}')

        if isinstance(c, libtcod.color.Color) is False:
            print("We didn't end up with a colour!")

    except AttributeError:
        print("not a valid attribite")

    return c

class ScreenObject:

    BLANK_CHAR = ' '
    NONE_CHAR = 0

    def __init__(self, char: int, fg: int = libtcod.white, bg: int = libtcod.black):
        self.char = char
        self.fg = fg
        self.bg = bg

    def render(self, con, x:int, y:int):
        libtcod.console_put_char_ex(con, x, y, self.char, fore=self.fg, back=self.bg)

    def clear(self, con, x, y):
        libtcod.console_put_char(con, x, y, ' ', libtcod.BKGND_NONE)

class ScreenObject2DArray:

    def __init__(self, chars: list, fg: int = libtcod.white, bg: int = libtcod.black):
        self.chars = chars
        self.fg = fg
        self.bg = bg

    def render(self, con, x:int, y:int):
        for dx,col in enumerate(self.chars):
            for dy,char in enumerate(col):
                if type(char) == 'int':
                    char = chr(char)
                if char != ScreenObject.NONE_CHAR:
                    libtcod.console_put_char_ex(con, x + dx, y + dy, char, fore=self.fg, back=self.bg)

    def clear(self, con, x:int, y:int):
        for dy,row in enumerate(self.chars):
            for dx,char in enumerate(row):
                libtcod.console_put_char(con, x + dx, y + dy, ' ', libtcod.BKGND_NONE)


class ScreenObjectList:

    def __init__(self, char:str, positions : list, fg: int = libtcod.white, bg: int = libtcod.black):
        self.char = char
        self.positions = positions
        self.fg = fg
        self.bg = bg

    def render(self, con):
        for x,y in self.positions:
            if self.char != ScreenObject.NONE_CHAR:
                libtcod.console_put_char_ex(con, x, y, self.char, fore=self.fg, back=self.bg)


class ScreenString:

    def __init__(self, text: str, fg: int = libtcod.white, bg: int = libtcod.black, alignment: int = libtcod.LEFT):
        self.text = text
        self.fg = fg
        self.bg = bg
        self.alignment = alignment

    def render(self, con, x:int, y:int, alignment:int = None):
        if alignment is None:
            alignment = self.alignment
        con.default_fg = self.fg
        con.default_bg = self.bg
        libtcod.console_print_ex(con, x, y, flag=libtcod.BKGND_OVERLAY, alignment=alignment, fmt = self.text)


class ScreenStringRect:

    def __init__(self, text: str, width: int, height:int,
                 fg: int = libtcod.white, bg: int = libtcod.black,
                 alignment: int = libtcod.LEFT):
        self.text = text
        self.width = width
        self.height = height
        self.fg = fg
        self.bg = bg
        self.alignment = alignment

    def render(self, con, x:int, y:int, alignment:int = None):
        if alignment is None:
            alignment = self.alignment
        con.default_fg = self.fg
        con.default_bg = self.bg
        libtcod.console_print_rect_ex(con, x, y, self.width, self.height,
                                      flag=libtcod.BKGND_SET,
                                      alignment=alignment,
                                      fmt=self.text
                                      )

class TextEntryBox:
    """:param"""

    DEFAULT_LENGTH = 30

    ALPHA_KEYS = [i for i in range(ord('a'), ord('z')+1)]
    NUMERIC_KEY_PAD_VKS = [i for i in range(libtcod.KEY_KP0, libtcod.KEY_KP9 + 1)]

    def __init__(self, width: int = DEFAULT_LENGTH, height: int = 1, parent=0, xpos:int = 0, ypos:int =0):
        """
        :param width: display width of the text entry box
        :param height: display height of the text entry box
        :param parent: parent console that the text entry box will be blitted to
        :param xpos: x position on the parent console where the text entry box will appear
        :param ypos: y position on the parent console where the text entry box will appear
        """

        # Dimensions of the text entry box
        self.width = width
        self.height = height

        # Parent console and position to display text entry box
        self.parent_console = parent
        self.xpos = xpos
        self.ypos = ypos

        # FG and BG of text
        self.fg = libtcod.white
        self.bg = libtcod.black

        # Define allowable characters
        self.mask_ranges = (['0','9'],['a','z'],['A','Z'])
        self.mask_specials = "+,. "

        # Create a console to use as the text box entry
        self.con = libtcod.console_new(self.width, self.height)

    def build_input_mask(self):
        self.mask=[]
        for mask_range_start, mask_range_end in self.mask_ranges:
            self.mask.extend([char for char in range(ord(mask_range_start), ord(mask_range_end)+1)])
        self.mask.extend([ord(char) for char in self.mask_specials])

    def get_text(self, max_length:int = None) -> str:
        """
        :param max_length: maximum allowable length of text that can be entered
        """

        # If no max length specified then use the full size of the input box
        if max_length is None:
            max_length = self.width * self.height

        self.build_input_mask()

        self.con.default_fg = self.fg
        self.con.default_bg = self.bg

        print(f"Getting some text (max {max_length} chars)")
        print(f'Using mask {self.mask}')

        key = libtcod.Key()
        mouse = None

        text = ""
        typing = True
        cursor_on = True

        while typing:

            libtcod.sys_sleep_milli(50)

            # Clear the text box
            libtcod.console_clear(self.con)

            # Print out what the user has currently entered
            dtext = (text + "*" if cursor_on else text)
            cursor_on = not cursor_on

            for y, l in enumerate(textwrap.wrap(dtext, self.width)):
                self.con.print_(0, y, l)

            # Process key release events
            libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS, key, mouse)

            # If a key was pressed...
            if key.vk != libtcod.KEY_NONE:

                # If enter pressed then we are done!
                if key.vk in (libtcod.KEY_ENTER, libtcod.KEY_KPENTER):
                    typing = False
                # If backspace pressed the delete last character
                elif key.vk == libtcod.KEY_BACKSPACE:
                    text = text[:-1]
                # If ESC pressed then we are done but no typing!
                elif key.vk == libtcod.KEY_ESCAPE:
                    typing = False
                    text = ""
                # If we have not hit the max length for the entered text...
                elif len(text) < max_length:
                    # If the pressed key is in our input mask then append to text
                    if key.c in self.mask:
                        if key.c in TextEntryBox.ALPHA_KEYS and key.shift is True:
                            text += chr(key.c).upper()
                        else:
                            text += chr(key.c)
                    # If the numeric pad was used...
                    elif key.vk in TextEntryBox.NUMERIC_KEY_PAD_VKS:
                        c = str(key.vk - libtcod.KEY_KP0)[0]
                        if ord(c) in self.mask:
                            text += c

            # Blit the text box console to the parent console
            libtcod.console_blit(self.con, 0, 0, self.width, self.height, self.parent_console, self.xpos, self.ypos)

            # Flush the parent console
            libtcod.console_flush(self.parent_console)

        return text


class Boxes:
    BORDER_DEFAULT = "default"
    BORDER_TYPE_1 = "type1"
    BORDER_TYPE_2 = "type2"
    BORDER_TYPE_3 = "type3"

    BORDER_TL = 0
    BORDER_T = 1
    BORDER_TR = 2
    BORDER_L = 3
    BORDER_M = 4
    BORDER_R = 5
    BORDER_BL = 6
    BORDER_B = 7
    BORDER_BR = 8
    BORDER_H = 9
    BORDER_V = 10

    BORDER_CHAR_MAPS = {

        BORDER_TYPE_1: (218, 194, 191, 195, 197, 180, 192, 193, 217, 196, 179),
        BORDER_TYPE_2: (201, 203, 187, 204, 206, 185, 200, 202, 188, 205, 186),
        BORDER_TYPE_3: (43, 43, 43, 43, 43, 43, 43, 43, 43, 124,45),
        BORDER_DEFAULT: [ord('#') for i in range(11)]
    }

    def __init__(self):
        pass

    @staticmethod
    def get_box(width, height, border_type: str = BORDER_DEFAULT):

        border_char_map = Boxes.BORDER_CHAR_MAPS.get(border_type)

        if border_char_map is None:
            border_char_map = Boxes.BORDER_CHAR_MAPS.get(Boxes.BORDER_DEFAULT)

        assert(border_char_map is not None)

        box = np.full((width, height), ord('#'))
        box[0,0] = border_char_map[Boxes.BORDER_TL]
        box[width-1, 0] = border_char_map[Boxes.BORDER_TR]
        box[0, height-1] = border_char_map[Boxes.BORDER_BL]
        box[width-1, height - 1] = border_char_map[Boxes.BORDER_BR]
        box[1:-1, 0] = border_char_map[Boxes.BORDER_H]
        box[1:-1, height-1] = border_char_map[Boxes.BORDER_H]
        box[0,1:-1] = border_char_map[Boxes.BORDER_V]
        box[width-1, 1:-1] = border_char_map[Boxes.BORDER_V]
        box[1:-1, 1:-1] = 0

        return box

    @staticmethod
    def box_to_text(box: np.array)->str:
        w,h = box.shape
        box_text=""
        for x in range(w):
            for y in range(h):
                c = box[x,y]
                box_text+= chr(box[x,y]) if c != 0 else " "
            box_text+="\n"

        return box_text

if __name__ == "__main__":

    # Test out the Boxes.get_box() static method
    box = Boxes.get_box(10,6, border_type=Boxes.BORDER_DEFAULT)
    print(Boxes.box_to_text(box))

    box = Boxes.get_box(10,6,border_type=Boxes.BORDER_TYPE_1)
    print(Boxes.box_to_text(box))

    box = Boxes.get_box(10,6,border_type=Boxes.BORDER_TYPE_2)
    print(Boxes.box_to_text(box))

    box = Boxes.get_box(10,6,border_type=Boxes.BORDER_TYPE_3)
    print(Boxes.box_to_text(box))