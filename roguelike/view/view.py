from roguelike import model
from .view_utils import *


class View():

    events = None

    def __init__(self, width:int=0, height:int=0):
        self.width=width
        self.height=height
        self.tick_count = 0

    @property
    def center(self):
        return (int(self.width/2), int(self.height/2))

    def tick(self):
        self.tick_count += 0

    def process_event(self, new_event: model.Event):
        print(f'{__class__} processing event {new_event}')

    def draw(self):
        pass

    @staticmethod
    def set_event_queue(new_q : model.EventQueue):
        View.events = new_q


class MainFrame(View):

    MODE_READY= "ready"
    MODE_PLAYING = "playing"
    MODE_INVENTORY_SCREEN = "inventory"
    MODE_CHARACTER_SCREEN = "character"
    MODE_PAUSED = "paused"

    CONSOLE_MESSAGE_PANEL_HEIGHT = 10
    CONSOLE_MESSAGE_PANEL_WIDTH = 50

    def __init__(self, width: int = 50, height: int = 50):

        super().__init__(width=width, height=height)
        # Properties
        self.mode = MainFrame.MODE_PLAYING

        # Components
        self.game = None
        self.con = None
        self.floor_view = FloorView(self.width, self.height, bg=libtcod.black)
        self.message_panel = MessagePanel(MainFrame.CONSOLE_MESSAGE_PANEL_WIDTH,
                                          MainFrame.CONSOLE_MESSAGE_PANEL_HEIGHT,
                                          fg=libtcod.white,
                                          bg=libtcod.black,
                                          border_bg=libtcod.black,
                                          border_fg=libtcod.green)

        self.inventory_view = InventoryView(width=int(self.width/2),
                                            height=int(self.height*2/3),
                                          fg=libtcod.white,
                                          bg=libtcod.black,
                                          border_bg=libtcod.black,
                                          border_fg=libtcod.green)

        self.character_view = CharacterView(width=int(self.width/2),
                                            height=int(self.height*2/3),
                                          fg=libtcod.white,
                                          bg=libtcod.black,
                                          border_bg=libtcod.black,
                                          border_fg=libtcod.green)

        self.text_entry = TextEntryBox()

    def initialise(self, model: model.Model):

        self.set_mode(MainFrame.MODE_PLAYING)

        self.game = model
        font_file_dir = ".\\roguelike\\view\\fonts\\"

        font_file_specs = {
            "dejavu_wide16x16_gs_tc.png": libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD,
            "dundalk12x12_gs_tc.png": libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD,
            "polyducks_12x12.png": libtcod.FONT_LAYOUT_ASCII_INROW,
            "terminal8x12_gs_ro.png": libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_ASCII_INROW
        }

        font_file = "polyducks_12x12.png"
        #font_file = "dejavu_wide16x16_gs_tc.png"
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
        self.message_panel.initialise()
        self.message_panel.add_message(f"Welcome to {self.game.name}")
        self.inventory_view.initialise(self.game.player)
        self.character_view.initialise(self.game.player)

    def set_mode(self, new_mode:str):
        self.mode = new_mode

    def process_event(self, new_event: model.Event):

        super().process_event(new_event)

        if new_event.type == model.Event.GAME:
            if new_event.name == model.Event.GAME_NEW_FLOOR:
                self.floor_view.initialise(floor=self.game.current_floor)

        self.floor_view.process_event(new_event)
        self.message_panel.process_event(new_event)

        if self.mode == MainFrame.MODE_INVENTORY_SCREEN:
            self.inventory_view.process_event(new_event)
        elif self.mode == MainFrame.MODE_CHARACTER_SCREEN:
            self.character_view.process_event(new_event)

    def draw(self):

        self.con.default_bg = libtcod.black
        libtcod.console_clear(self.con)

        # If we are playing then draw the current floor, etc.
        if self.mode == MainFrame.MODE_PLAYING:

            self.floor_view.draw()
            self.message_panel.draw()

            # Blit the current floor
            libtcod.console_blit(self.floor_view.con,
                                 0, 0,
                                 self.floor_view.width, self.floor_view.height,
                                 0,
                                 0, 0, ffade=1, bfade=1)

            # Blit the message panel
            libtcod.console_blit(self.message_panel.con,
                                 0, 0,
                                 self.message_panel.width,
                                 self.message_panel.height,
                                 0,
                                 0, self.height-MainFrame.CONSOLE_MESSAGE_PANEL_HEIGHT,
                                 ffade=0.7, bfade=0.7)

        # If we are in INVENTORY mode the draw the inventory screen
        elif self.mode == MainFrame.MODE_INVENTORY_SCREEN:
            self.inventory_view.draw()
            bx = int((self.width - self.inventory_view.width)/2)
            by = int((self.height - self.inventory_view.height) / 2)
            # Blit the inventory panel
            libtcod.console_blit(self.inventory_view.con,
                                 0,0,
                                 self.inventory_view.width,
                                 self.inventory_view.height,
                                 0,
                                 bx, by,
                                 ffade=1, bfade=1)

        # If we are in CHARACTER mode then draw the character screen
        elif self.mode == MainFrame.MODE_CHARACTER_SCREEN:
            # Redraw the character view
            self.character_view.draw()
            bx = int((self.width - self.character_view.width)/2)
            by = int((self.height - self.character_view.height) / 2)
            # Blit the character panel
            libtcod.console_blit(self.character_view.con,
                                 0,0,
                                 self.character_view.width,
                                 self.character_view.height,
                                 0,
                                 bx, by,
                                 ffade=1, bfade=1)

        # Otherwise just display current mode in a box!!!
        else:
            # Draw box with current game mode
            bw = int(self.width/2)
            bh = 5
            bx = int((self.width - bw)/2)
            by = int((self.height - bh)/2)

            # Draw the border
            border = Boxes.get_box(width=bw, height=bh, border_type=Boxes.BORDER_TYPE_1, fill_char=ord(' '))
            border = Boxes.get_box(width=bw, height=bh, border_type=Boxes.BORDER_TYPE_1)
            bo = ScreenObject2DArray(border, fg=libtcod.white, bg=libtcod.red)
            bo.render(0, bx, by)

            panel_text = self.mode.upper()
            # Print the panel text
            so = ScreenString(panel_text,
                                  fg=libtcod.yellow,
                                  bg=libtcod.darkest_gray)
            so.render(0, bw, by+2, alignment=libtcod.CENTER)

            #Add game title

            bw = int(self.width/2)
            bh = 5
            bx = int((self.width - bw)/2)
            by = 1
            box = Boxes.get_box(bw,bh, border_type=Boxes.BORDER_TYPE_1)
            bo = ScreenObject2DArray(box, fg=libtcod.green, bg=libtcod.grey)
            bo.render(0, bx, 1)

            panel_text="Rogue Tower"
            so = ScreenString(panel_text,
                                  fg=libtcod.darker_green,
                                  bg=libtcod.darkest_gray)
            so.render(0, bw, by+2, alignment=libtcod.CENTER)

        libtcod.console_flush()

    def add_message(self, new_message : str):
        self.message_panel.add_message(new_message)

    def do_text_entry(self):
        text_entry_box = TextEntryBox(width=20, height=3, parent = self.con, xpos=10, ypos=10)
        text_entry_box.fg = libtcod.red
        text_entry_box.bg = libtcod.white
        #text_entry_box.mask_ranges = [('0','9')]

        return text_entry_box.get_text(20)

class FloorView(View):
    def __init__(self, width: int, height: int, fg = libtcod.white, bg=libtcod.black):
        super().__init__(width=width, height=height)

        self.con = None

        # Appearance of the view content
        self.fg = fg
        self.bg = bg
        self.bg_lit_path = libtcod.darker_yellow
        self.bg_lit_wall = libtcod.darkest_yellow
        self.bg_explored_path = libtcod.darker_grey
        self.bg_explored_wall = libtcod.darkest_grey

        # Model Floor that we are going to render
        self.floor = None

    def initialise(self, floor: model.Floor):
        # Connect the view to the model
        self.floor = floor

        # Create a new console to draw on
        self.con = libtcod.console_new(self.width, self.height)

    def draw(self):

        # Clear the screen with the background colour
        self.con.default_bg = self.bg
        libtcod.console_clear(self.con)

        # Get the types of cells that we need to draw
        explored_cells = self.floor.get_explored_cells()
        fov_cells = self.floor.get_fov_cells()
        walkable_cells = self.floor.get_walkable_cells()

        # Loop through all of the cells that we have already explored
        for x,y in explored_cells:

            # For the cells in the current FOV
            if (x, y) in fov_cells:
                # Lit path
                if (x,y) in walkable_cells:
                    libtcod.console_set_char_background(self.con, x, y, self.bg_lit_path)
                # Else lit wall
                else:
                    libtcod.console_set_char_background(self.con, x, y, self.bg_lit_wall)
            else:
                # Unlit path
                if (x,y) in walkable_cells:
                    libtcod.console_set_char_background(self.con, x, y, self.bg_explored_path)
                # Else unlit wall
                else:
                    libtcod.console_set_char_background(self.con, x, y, self.bg_explored_wall)

        # Draw all of the entities in the current FOV
        fov_entities = [e for e in self.floor.entities if e.xy in fov_cells]
        if len(fov_entities) > 0:
            entities = sorted(fov_entities, key = lambda x: x.get_property("Zorder"), reverse=True)
            for e in entities:
                x, y = e.xy
                bg = e.bg
                try:
                    libtcod.console_set_default_foreground(self.con, e.fg)
                    libtcod.console_put_char(self.con, x, y, e.char, libtcod.BKGND_NONE)
                    if bg is not None:
                        libtcod.console_set_char_background(self.con, x, y, bg)
                except e:
                    print("Problem drawing {e.name} {e.fg} {e.bg}")
                    print(e)

        # Draw the player
        so = ScreenObject('@', fg=libtcod.dark_sea, bg=self.bg_lit_path)
        so.render(self.con, x=self.floor.player.x, y=self.floor.player.y)

        # Draw name of current room
        room_name = self.floor.current_room.name if self.floor.current_room is not None else "???"
        s = ScreenString(f'{self.floor.name}:{room_name}', fg=libtcod.red, bg=libtcod.white)
        s.render(self.con, 0, 0, alignment=libtcod.LEFT)


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





class MessagePanel(View):

    BORDER_TYPE1 = "type1"
    BORDER_TYPE2 = "type2"

    def __init__(self, width: int, height: int,
                 fg = libtcod.white, bg=libtcod.black,
                 border_fg = libtcod.white, border_bg=libtcod.black):

        super().__init__(width=width, height=height)
        self.fg = fg
        self.bg = bg
        self.border_fg = border_fg
        self.border_bg = border_bg

        self.con = None
        self.messages=[]

        self.border_type = MessagePanel.BORDER_TYPE1
        self.border = None

    def initialise(self):
        self.con = libtcod.console_new(self.width, self.height)
        self.border = Boxes.get_box(self.width, self.height, border_type=self.border_type)

    def add_message(self, new_message : str):
        self.messages.append(new_message)
        if len(self.messages) > self.height:
            del self.messages[0]

    def process_event(self, new_event: model.Event):
        self.add_message(new_event.description)

    def draw(self):

        # Clear the screen with the background colour
        self.con.default_bg = self.bg
        libtcod.console_clear(self.con)

        # Draw the border
        bo = ScreenObject2DArray(self.border, fg=self.border_fg, bg=self.border_bg)
        bo.render(self.con, 0, 0)

        panel_text = ""
        for message in self.messages[-1:0:-1]:
            panel_text += message+"\n"

        # Print the panel text
        so = ScreenStringRect(panel_text,
                              width = self.width-2,
                              height = self.height-2,
                              fg=self.fg,
                              bg=self.bg)

        so.render(self.con, 1, 1)


class InventoryView(View):
    BORDER_TYPE1 = "type1"
    BORDER_TYPE2 = "type2"

    def __init__(self, width: int, height: int,
                 fg=libtcod.white, bg=libtcod.black,
                 border_fg=libtcod.white, border_bg=libtcod.black):

        super().__init__(width=width, height=height)

        # Properties
        self.fg = fg
        self.bg = bg
        self.border_fg = border_fg
        self.border_bg = border_bg
        self.border_type = InventoryView.BORDER_TYPE1

        # Components
        self.con = None
        self.character = None
        self.selected_item = -1
        self.selected_item_entity = None
        self.message_event = None
        self.border = None

    def initialise(self, character : model.Entity):

        self.character = character

        self.con = libtcod.console_new(self.width, self.height)
        self.border = Boxes.get_box(self.width, self.height, border_type=self.border_type)

    def process_event(self, new_event: model.Event):
        print(f'{__class__}: Event {new_event}')
        if new_event.name in (model.Event.ACTION_SUCCEEDED, model.Event.ACTION_FAILED):
            self.message_event = new_event
        else:
            self.message_event = None

    def change_selection(self, d : int):

        self.message_event = None

        inventory = self.character.inventory.get_other_items()
        inventory_stackable = self.character.inventory.get_stackable_items()
        self.selected_item += d
        self.selected_item = min(max(0,self.selected_item), len(inventory) + len(inventory_stackable) -1)

    def get_selected_item(self):

        return self.selected_item_entity

    def draw(self):

        cc = self.character.fighter.combat_class
        equipment = self.character.fighter.equipment

        equipment_stat_names = ("AC", "Weight")
        equipment_totals = self.character.fighter.get_equipment_stat_totals(equipment_stat_names)
        print(equipment_totals)
        inv = self.character.inventory
        inventory = self.character.inventory.get_other_items()
        inventory_stackable =  self.character.inventory.get_stackable_items()

        if inv.items > 0:
            self.selected_item = min(max(0,self.selected_item), inv.items -1)
        else:
            self.selected_item = -1
            self.selected_item_entity = None

        cx, cy = self.center

        # Clear the screen with the background colour
        self.con.default_bg = self.bg
        libtcod.console_clear(self.con)

        # Draw the border
        bo = ScreenObject2DArray(self.border, fg=self.border_fg, bg=self.border_bg)
        bo.render(self.con, 0, 0)

        # Create a box divider
        divider_box = Boxes.get_box_divider(length=self.width, border_type=self.border_type)
        divider = ScreenObject2DArray(divider_box, fg=self.border_fg, bg=self.border_bg)

        y=2

        text = f"Inventory for {self.character.name} the {cc.name}"

        # Print the panel text
        so = ScreenStringRect(text,
                              width=self.width - 2,
                              height=self.height - 2,
                              fg=self.fg,
                              bg=self.bg,
                              alignment=libtcod.CENTER)

        so.render(self.con, cx, y)

        y+=2

        # Draw a divider
        divider.render(self.con, 0, y)

        y+=2

        # Print what is currently equipped
        text = f'Equipment: AC={equipment_totals["AC"]}, Weight={equipment_totals["Weight"]}'

        # Print the panel text
        so = ScreenStringRect(text,
                              width=self.width - 2,
                              height=self.height - 2,
                              fg=self.fg,
                              bg=self.bg,
                              alignment=libtcod.CENTER)

        so.render(self.con, cx, y)

        y+=2

        if len(equipment) == 0:

            text = "Nothing"
            so = ScreenStringRect(text,
                                  width=self.width - 2,
                                  height=self.height - 2,
                                  fg=self.fg,
                                  bg=self.bg,
                                  alignment=libtcod.CENTER)

            so.render(self.con, cx, y)

        else:

            for slot, item in equipment.items():

                text=f'{slot}: {item.description}'
                # Print the panel text
                so = ScreenString(text,
                                  fg=self.fg,
                                  bg=self.bg,
                                  alignment=libtcod.CENTER)

                so.render(self.con, cx, y)
                y += 1

        y+=1

        # Draw a divider
        divider.render(self.con, 0, y)

        y+=2

        # Print what items are being carried
        text = f"Carrying {inv.items} item(s) (max {inv.max_items})"

        so = ScreenStringRect(text,
                              width=self.width - 2,
                              height=self.height - 2,
                              fg=self.fg,
                              bg=self.bg,
                              alignment=libtcod.CENTER)

        so.render(self.con, cx, y)

        y+=2

        if inv.items == 0:
            text = "Nothing"
            so = ScreenStringRect(text,
                                  width=self.width - 2,
                                  height=self.height - 2,
                                  fg=libtcod.light_yellow,
                                  bg=self.bg,
                                  alignment=libtcod.CENTER)

            so.render(self.con, cx, y)

        for i, item in enumerate(inventory):

            if i == self.selected_item:
                bg=libtcod.red
                fg=libtcod.black
                self.selected_item_entity = item
            else:
                bg=libtcod.black
                fg=libtcod.yellow

            text=f'{item.description}'
            so = ScreenString(text,
                              fg=fg,
                              bg=bg,
                              alignment=libtcod.CENTER)

            so.render(self.con, cx, y)
            y += 1

        for i, (item, count) in enumerate(inventory_stackable.items()):

            if i == (self.selected_item - len(inventory)):
                bg=libtcod.red
                fg=libtcod.black
                self.selected_item_entity = item
            else:
                bg=libtcod.black
                fg=libtcod.yellow

            text=f'{item.description}: {count}'
            # Print the panel text
            so = ScreenString(text,
                              fg=fg,
                              bg=bg,
                              alignment=libtcod.CENTER)

            so.render(self.con, cx, y)
            y += 1


        # Print any event messages that we have received
        y= self.height - 4

        # Draw a divider
        divider.render(self.con, 0, y)

        if self.message_event is not None:
            message_text = self.message_event.description
            if self.message_event.name == model.Event.ACTION_FAILED:
                fg = libtcod.lighter_yellow
            else:
                fg = libtcod.white

            so = ScreenStringRect(message_text,
                                  width=self.width - 2,
                                  height=2,
                                  fg=fg,
                                  bg=self.bg,
                                  alignment=libtcod.CENTER)

            so.render(self.con, int(self.width/2), self.height-3)


class CharacterView(View):
    BORDER_TYPE1 = "type1"
    BORDER_TYPE2 = "type2"

    def __init__(self, width: int, height: int,
                 fg=libtcod.white, bg=libtcod.black,
                 border_fg=libtcod.white, border_bg=libtcod.black):

        super().__init__(width=width, height=height)

        self.fg = fg
        self.bg = bg
        self.border_fg = border_fg
        self.border_bg = border_bg

        self.con = None
        self.character = None

        self.border_type = CharacterView.BORDER_TYPE2
        self.border = None

    def initialise(self, character : model.Entity):

        self.character = character

        self.con = libtcod.console_new(self.width, self.height)
        self.border = Boxes.get_box(self.width, self.height, border_type=self.border_type)

    def process_event(self, new_event: model.Event):
        pass

    def draw(self):

        entity_stats = self.character.properties
        cc = self.character.fighter.combat_class

        # Character Equipment stats
        equipment_stat_names = ("AC", "Weight")
        equipment_totals = self.character.fighter.get_equipment_stat_totals(equipment_stat_names)
        print(equipment_totals)
        ac = self.character.get_stat_total("AC")
        print(f'Total AC={ac}')

        # Clear the screen with the background colour
        self.con.default_bg = self.bg
        libtcod.console_clear(self.con)

        cx, cy = self.center

        # Draw the border
        bo = ScreenObject2DArray(self.border, fg=self.border_fg, bg=self.border_bg)
        bo.render(self.con, 0, 0)

        # Create a box divider
        divider_box = Boxes.get_box_divider(length=self.width, border_type=self.border_type)
        divider = ScreenObject2DArray(divider_box, fg=self.border_fg, bg=self.border_bg)

        y=2
        text = f"Character Sheet for {self.character.name} the {cc.name}"

        so = ScreenString(text,
                              fg=self.fg,
                              bg=self.bg,
                              alignment=libtcod.CENTER)

        so.render(self.con, cx, y)

        y+=2

        # Draw a divider
        divider.render(self.con, 0, y)

        y+=2

        for stat, value in cc.properties.items():
            text=f'{stat}: {value}'
            # Print the panel text
            so = ScreenString(text,
                              fg=self.fg,
                              bg=self.bg,
                              alignment=libtcod.CENTER)

            so.render(self.con, cx, y)
            y += 1


        y+=1

        # Draw a divider
        divider.render(self.con, 0, y)

        y+=2

        # Print what is currently equipped
        text = f'Equipment: AC={equipment_totals["AC"]}, Weight={equipment_totals["Weight"]}'

        so = ScreenString(text,
                              fg=self.fg,
                              bg=self.bg,
                              alignment=libtcod.CENTER)

        so.render(self.con, cx, y)

        y+=2

        # Draw a divider
        divider.render(self.con, 0, y)

        y+=2

        text = f"Stats:"

        # Print the panel text
        so = ScreenStringRect(text,
                              width=self.width - 2,
                              height=self.height - 2,
                              fg=self.fg,
                              bg=self.bg,
                              alignment=libtcod.CENTER)

        so.render(self.con, cx, y)

        y+=2
        for stat, value in entity_stats:
            text=f'{stat}: {value}'
            # Print the panel text
            so = ScreenString(text,
                              fg=self.fg,
                              bg=self.bg,
                              alignment=libtcod.CENTER)

            so.render(self.con, cx, y)
            y += 1

