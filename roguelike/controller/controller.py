import roguelike.model as model
import roguelike.view as view
import tcod as libtcod
import numpy as np

class Controller():

    GAME_MODE_START = "start"
    GAME_MODE_CHARACTER_CREATION = "character creation"
    GAME_MODE_INVENTORY = "inventory"
    GAME_MODE_CHARACTER = "character"
    GAME_MODE_PLAYING = "playing"
    GAME_MODE_PAUSED = "paused"
    GAME_MODE_GAME_OVER = "game over"

    def __init__(self, name:str):
        #Properties
        self.name = name
        self.mode = None

        # Components
        self.view = None
        self.model = None
        self.events = None

    def initialise(self):
        self.model = model.Model(self.name)
        self.model.initialise()
        self.events = self.model.events

        self.view = view.MainFrame(50,65)
        self.view.initialise(self.model)
        self.view.set_event_queue(self.model.events)
        self.set_mode(Controller.GAME_MODE_START)

        self.events.add_event(model.Event(type=model.Event.CONTROL,
                                    name=model.Event.STATE_LOADED,
                                    description="Hit 'N' to create a new character"))

    def set_mode(self, new_mode):

        if new_mode != self.mode:

            self.last_mode = self.mode
            self.mode = new_mode

            if new_mode == Controller.GAME_MODE_START:
                self.view.set_mode(view.MainFrame.MODE_READY)
                self.model.set_mode(model.Model.GAME_STATE_PAUSED)

            elif new_mode == Controller.GAME_MODE_INVENTORY:
                self.view.set_mode(view.MainFrame.MODE_INVENTORY_SCREEN)
                self.model.set_mode(model.Model.GAME_STATE_PAUSED)

            elif new_mode == Controller.GAME_MODE_CHARACTER:
                self.view.set_mode(view.MainFrame.MODE_CHARACTER_SCREEN)
                self.model.set_mode(model.Model.GAME_STATE_PAUSED)

            elif new_mode == Controller.GAME_MODE_CHARACTER_CREATION:
                self.view.set_mode(view.MainFrame.MODE_CHARACTER_CREATION_SCREEN)
                self.model.set_mode(model.Model.GAME_STATE_PAUSED)

            elif new_mode == Controller.GAME_MODE_PLAYING:
                self.view.set_mode(view.MainFrame.MODE_PLAYING)
                self.model.set_mode(model.Model.GAME_STATE_PLAYING)

            elif new_mode == Controller.GAME_MODE_PAUSED:
                self.view.set_mode(view.MainFrame.MODE_PAUSED)
                self.model.set_mode(model.Model.GAME_STATE_PAUSED)

            if new_mode == Controller.GAME_MODE_GAME_OVER:
                self.view.set_mode(view.MainFrame.MODE_GAME_OVER)
                self.model.set_mode(model.Model.GAME_STATE_PAUSED)



    def run(self):

        key = libtcod.Key()
        mouse = libtcod.Mouse()

        while not libtcod.console_is_window_closed():

            # Loop to process game events
            event = self.model.get_next_event()
            while event is not None:
                self.view.process_event(event)

                if event.type == model.Event.STATE and event.name == model.Event.STATE_GAME_OVER:
                    self.set_mode(Controller.GAME_MODE_GAME_OVER)

                event = self.model.get_next_event()

            # Draw the view
            self.view.draw()

            # Wait for event.........
            libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS, key, mouse)
            #key = libtcod.console_wait_for_keypress(True)
            action = self.handle_keys(key)

            if action is None:
                print(f'key={key}, mode={self.mode}')

            #print(f'Game Mode={self.mode}; last mode={self.last_mode}')

            # Common actions
            exit = action.get('exit')
            fullscreen = action.get('fullscreen')
            move = action.get('move')
            use = action.get('use')
            debug = action.get('debug')

            if debug is True:
                self.model.print()

            # If we are in PLAYING mode
            if self.mode == Controller.GAME_MODE_PLAYING:
                player_turn = True

                # Game playing actions
                wait = action.get('wait')
                fullscreen = action.get('fullscreen')
                stairs = action.get('take stairs')
                pickup = action.get('pickup')
                inventory = action.get('show_inventory')
                character = action.get('show_character')
                pause = action.get('pause')

                if move:
                    dx, dy = move
                    self.model.move_player(dx,dy)
                    player_turn = False
                elif stairs:
                    self.model.take_stairs()
                    player_turn = False
                elif pickup:
                    self.model.take_item()
                elif use:
                    self.model.use_item()
                elif inventory:
                    self.set_mode(Controller.GAME_MODE_INVENTORY)
                elif character:
                    self.set_mode(Controller.GAME_MODE_CHARACTER)
                elif pause:
                    self.set_mode(Controller.GAME_MODE_PAUSED)
                elif wait:
                    player_turn = False

                if player_turn is False:
                    # Tick the model
                    libtcod.sys_sleep_milli(100)
                    self.model.tick()

            # If we are in START mode
            elif self.mode == Controller.GAME_MODE_START:
                new_game = action.get('new_game')
                new_character = action.get("new_character")

                if new_game:
                    self.set_mode(Controller.GAME_MODE_PLAYING)
                elif new_character:
                    self.set_mode(Controller.GAME_MODE_CHARACTER_CREATION)
                elif exit:
                    return True

            # If we are in CHARACTER mode
            elif self.mode == Controller.GAME_MODE_CHARACTER:

                level_up = action.get('level-up')

                if move:
                    dx, dy = move
                    self.view.character_view.change_selection(dy)

                elif level_up:
                    stat_name = self.view.character_view.get_selected_stat()
                    self.model.level_up(stat_name)

            # If we are in CHARACTER CREATION mode
            elif self.mode == Controller.GAME_MODE_CHARACTER_CREATION:

                edit_name = action.get('edit_name')
                edit_class = action.get('edit_class')
                select = action.get("select")

                if edit_name:
                    self.view.character_creation_view.mode = view.CreateCharacterView.MODE_NAME_PICK
                elif edit_class:
                    self.view.character_creation_view.mode = view.CreateCharacterView.MODE_CLASS_PICK
                elif move:
                    dx, dy = move
                    self.view.character_creation_view.change_selection(dy)
                elif select:
                    if self.view.character_creation_view.mode == view.CreateCharacterView.MODE_CLASS_PICK:
                        name = self.view.character_creation_view.character_name
                        class_name = self.view.character_creation_view.get_selected_class()
                        self.model.add_player(self.model.generate_player(name, class_name))
                        self.view.character_creation_view.initialise(self.model)
                        self.view.character_creation_view.mode = view.CreateCharacterView.MODE_DISPLAY_CHARACTER


                # else:
                #     self.view.character_creation_view.mode = view.CreateCharacterView.MODE_DISPLAY_CHARACTER


            # If we are in INVENTORY mode
            elif self.mode == Controller.GAME_MODE_INVENTORY:
                equip = action.get('equip')
                drop = action.get('drop')

                e = self.view.inventory_view.get_selected_item()

                if move:
                    dx, dy = move
                    self.view.inventory_view.change_selection(dy)
                else:

                    if e is None:
                        self.events.add_event(model.Event(type=model.Event.GAME,
                                                    name=model.Event.ACTION_FAILED,
                                                    description=f"No item selected!"))
                    elif equip:
                        self.model.equip_item(e)
                    elif drop:
                        self.model.drop_item(e)
                    elif use:
                        self.model.use_item(e)

            # If we are in GAME PAUSED mode
            elif self.mode == Controller.GAME_MODE_PAUSED:
                play = action.get("play")

                if exit:
                    self.set_mode(Controller.GAME_MODE_GAME_OVER)
                    continue
                if play:
                    self.set_mode(Controller.GAME_MODE_PLAYING)

            # If we are in GAME OVER mode
            elif self.mode == Controller.GAME_MODE_GAME_OVER:
                start = action.get("start")
                if start:
                    self.initialise()
                    self.set_mode(Controller.GAME_MODE_START)

            if exit:
                self.set_mode(self.last_mode)

            if fullscreen:
                libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())



    def handle_keys(self, key):

        if self.mode == Controller.GAME_MODE_START:
            return self.handle_start_menu_keys(key)

        elif self.mode == Controller.GAME_MODE_PLAYING:
            return self.handle_player_turn_keys(key)

        elif self.mode == Controller.GAME_MODE_PAUSED:
            return self.handle_game_paused_keys(key)

        elif self.mode == Controller.GAME_MODE_INVENTORY:
            return self.handle_inventory_keys(key)

        elif self.mode == Controller.GAME_MODE_CHARACTER:
            return self.handle_character_view_keys(key)

        elif self.mode == Controller.GAME_MODE_CHARACTER_CREATION:
            return self.handle_create_character_view_keys(key)

        elif self.mode == Controller.GAME_MODE_GAME_OVER:
            return self.handle_game_over_keys(key)


        # No key was pressed
        return {}

    def handle_start_menu_keys(self, key):
        key_char = chr(key.c)
        if key_char == 'a' or key.vk == libtcod.KEY_SPACE:
            return {'new_game': True}
        elif key_char == 'n':
            return {'new_character': True}
        elif key.vk == libtcod.KEY_ESCAPE:
            return {'exit': True}

        return {}

    def handle_player_turn_keys(self, key):

        key_char = chr(key.c)

        # Movement keys
        if key.vk == libtcod.KEY_UP:
            return {'move': (0, -1)}
        elif key.vk == libtcod.KEY_DOWN:
            return {'move': (0, 1)}
        elif key.vk == libtcod.KEY_LEFT:
            return {'move': (-1, 0)}
        elif key.vk == libtcod.KEY_RIGHT:
            return {'move': (1, 0)}
        elif key.vk == libtcod.KEY_ENTER:
            return {'take stairs': True}
        elif key_char == 'g':
            return {'pickup': True}
        elif key_char == 'z':
            return {'wait': True}
        elif key_char == 'u':
            return {'use': True}
        elif key_char == 'i':
            return {'show_inventory': True}
        elif key_char == 'c':
            return {'show_character': True}
        elif key_char == 'd':
            return {'drop_inventory': True}

        if key.vk == libtcod.KEY_ENTER and key.lalt:
            # Alt+Enter: toggle full screen
            return {'fullscreen': True}
        elif key.vk == libtcod.KEY_ESCAPE:
            return {'pause': True}
        elif key.vk == libtcod.KEY_F12:
            te = TextEntry()
            text = te.get_text()
            print(text)
            self.view.add_message(text)
        elif key.vk == libtcod.KEY_F11:
            return {'debug': True}
        elif key.vk == libtcod.KEY_F10:
            self.model.next_floor()

        # No key was pressed
        return {}

    def handle_inventory_keys(self, key):
        key_char = chr(key.c)

        if key.vk == libtcod.KEY_ENTER and key.lalt:
            # Alt+Enter: toggle full screen
            return {'fullscreen': True}
        # Movement keys
        elif key.vk == libtcod.KEY_UP:
            return {'move': (0, -1)}
        elif key.vk == libtcod.KEY_DOWN:
            return {'move': (0, 1)}
        elif key_char == 'e':
            return {'equip': True}
        elif key_char == 'd':
            return {'drop': True}
        elif key_char == 'u':
            return {'use': True}
        elif key.vk == libtcod.KEY_ESCAPE or key_char == "i":
            # Exit the menu
            return {'exit': True}

        return {}

    def handle_character_view_keys(self, key):
        key_char = chr(key.c)

        if key_char == 'l':
            return {'level-up': True}

        elif key.vk == libtcod.KEY_ENTER and key.lalt:
            # Alt+Enter: toggle full screen
            return {'fullscreen': True}
        # Movement keys
        elif key.vk == libtcod.KEY_UP:
            return {'move': (0, -1)}
        elif key.vk == libtcod.KEY_DOWN:
            return {'move': (0, 1)}
        elif key.vk == libtcod.KEY_ESCAPE or key_char == "c":
            # Exit the menu
            return {'exit': True}

        return {}

    def handle_create_character_view_keys(self, key):
        key_char = chr(key.c)

        if key.vk == libtcod.KEY_ENTER and key.lalt:
            # Alt+Enter: toggle full screen
            return {'fullscreen': True}
        elif key_char == "n":
            return {'edit_name': True}
        elif key_char == "c":
            return {'edit_class': True}
        elif key.vk == libtcod.KEY_UP:
            return {'move': (0, -1)}
        elif key.vk == libtcod.KEY_DOWN:
            return {'move': (0, 1)}
        elif key.vk == libtcod.KEY_ENTER:
            return {'select': True}
        elif key.vk == libtcod.KEY_ESCAPE or key_char == "c":
            # Exit the menu
            return {'exit': True}

        return {}

    def handle_game_paused_keys(self, key):
        key_char = chr(key.c)

        if key.vk == libtcod.KEY_ENTER and key.lalt:
            # Alt+Enter: toggle full screen
            return {'fullscreen': True}

        elif key.vk == libtcod.KEY_ESCAPE:
            # Exit paused mode
            return {'play': True}
        elif key_char == "q":
            return {'exit':True}

        return {}

    def handle_game_over_keys(self, key):
        key_char = chr(key.c)

        if key.vk == libtcod.KEY_ENTER and key.lalt:
            # Alt+Enter: toggle full screen
            return {'fullscreen': True}
        elif key.vk in (libtcod.KEY_ENTER, libtcod.KEY_SPACE):
            return {'start': True}
        elif key.vk == libtcod.KEY_ESCAPE or key_char == "c":
            # Exit the menu
            return {'exit': True}

        return {}

class TextEntry:
    def __init__(self):
        self.mask = np.concatenate((np.arange(ord('a'), ord('z')),
                                    np.arange(ord('A'), ord('Z')),
                                    np.arange(ord('0'), ord('9'))), axis=0)

    def get_text(self, max_length = 30):

        print(f"Getting some text (max {max_length} chars")
        print(f'Using mask {self.mask}')

        key = libtcod.Key()
        mouse = libtcod.Mouse()

        text=""

        typing = True
        while typing:
            libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS, key, mouse)
            if key.vk == libtcod.KEY_ENTER:
                typing = False
            elif len(text) < max_length and key.c in self.mask:
                text +=chr(key.c)
                print(text)
            elif key.vk == libtcod.KEY_BACKSPACE:
                text = text[:-1]
                print(text)

        return text