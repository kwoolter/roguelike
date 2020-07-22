import roguelike.model as model
import roguelike.view as view
import tcod as libtcod
import numpy as np

class Controller():

    GAME_MODE_START = "start"
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

        self.view = view.MainFrame(80,60)
        self.view.initialise(self.model)
        self.view.set_event_queue(self.model.events)
        self.set_mode(Controller.GAME_MODE_START)

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
            elif new_mode == Controller.GAME_MODE_PLAYING:
                self.view.set_mode(view.MainFrame.MODE_PLAYING)
                self.model.set_mode(model.Model.GAME_STATE_PLAYING)
            elif new_mode == Controller.GAME_MODE_PAUSED:
                self.view.set_mode(view.MainFrame.MODE_PAUSED)
                self.model.set_mode(model.Model.GAME_STATE_PAUSED)

    def run(self):

        key = libtcod.Key()
        mouse = libtcod.Mouse()

        while not libtcod.console_is_window_closed():

            # Loop to process game events
            event = self.model.get_next_event()
            while event is not None:
                self.view.process_event(event)
                event = self.model.get_next_event()

            # Draw the view
            self.view.draw()

            # Wait for event.........
            #libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS, key, mouse)
            key = libtcod.console_wait_for_keypress(True)
            action = self.handle_keys(key)

            #print(f'Game Mode={self.mode}; last mode={self.last_mode}')

            # Common actions
            exit = action.get('exit')
            fullscreen = action.get('fullscreen')
            move = action.get('move')

            # If we are in PLAYING mode
            if self.mode == Controller.GAME_MODE_PLAYING:
                # Game playing actions
                wait = action.get('wait')
                fullscreen = action.get('fullscreen')
                stairs = action.get('take stairs')
                pickup = action.get('pickup')
                inventory = action.get('show_inventory')
                character = action.get('show_character')

                if move:
                    dx, dy = move
                    self.model.move_player(dx,dy)
                elif stairs:
                    self.model.take_stairs()
                elif pickup:
                    self.model.take_item()
                elif inventory:
                    self.set_mode(Controller.GAME_MODE_INVENTORY)
                elif character:
                    self.set_mode(Controller.GAME_MODE_CHARACTER)
                elif exit:
                    self.set_mode(Controller.GAME_MODE_PAUSED)

            # If we are in PAUSED mode
            elif self.mode == Controller.GAME_MODE_PAUSED:
                if exit:
                    self.set_mode(Controller.GAME_MODE_START)
                    continue

            # If we are in START mode
            elif self.mode == Controller.GAME_MODE_START:
                new_game = action.get('new_game')

                if new_game:
                    self.set_mode(Controller.GAME_MODE_PLAYING)
                elif exit:
                    return True

            # If we are in INVENTORY mode
            elif self.mode == Controller.GAME_MODE_CHARACTER:
                level_up = action.get('level-up')

                if level_up:
                    self.model.player.level_up()

            # If we are in INVENTORY mode
            elif self.mode == Controller.GAME_MODE_INVENTORY:
                equip = action.get('equip')
                drop = action.get('drop')
                use = action.get('use')

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

            if exit:
                self.set_mode(self.last_mode)

            if fullscreen:
                libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

            # Tick the model
            self.model.tick()

    def handle_keys(self, key):

        if self.mode == Controller.GAME_MODE_START:
            return self.handle_start_menu_keys(key)
        elif self.mode == Controller.GAME_MODE_PLAYING:
            return self.handle_player_turn_keys(key)
        elif self.mode == Controller.GAME_MODE_INVENTORY:
            return self.handle_inventory_keys(key)
        elif self.mode == Controller.GAME_MODE_CHARACTER:
            return self.handle_character_view_keys(key)

        # No key was pressed
        return {}

    def handle_start_menu_keys(self, key):
        key_char = chr(key.c)
        if key_char == 'a' or key.vk == libtcod.KEY_SPACE:
            return {'new_game': True}
        elif key_char == 'b':
            return {'load_game': True}
        elif key_char == 'c' or key.vk == libtcod.KEY_ESCAPE:
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
            # Exit the game
            return {'exit': True}
        elif key.vk == libtcod.KEY_F12:
            te = TextEntry()
            text = te.get_text()
            print(text)
            self.view.add_message(text)
        elif key.vk == libtcod.KEY_F11:
            text = self.view.do_text_entry()
            self.view.add_message(text)
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
        elif key.vk == libtcod.KEY_ESCAPE:
            # Exit the menu
            return {'exit': True}

        return {}

    def handle_character_view_keys(self, key):
        key_char = chr(key.c)

        if key_char == 'l':
            return {'level-up': True}

        if key.vk == libtcod.KEY_ENTER and key.lalt:
            # Alt+Enter: toggle full screen
            return {'fullscreen': True}
        elif key.vk == libtcod.KEY_ESCAPE:
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