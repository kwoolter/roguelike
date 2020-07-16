import roguelike.model as model
import roguelike.view as view
import tcod as libtcod
import numpy as np

class Controller():
    def __init__(self, name:str):
        self.name = name
        self.view = None
        self.model = None

    def initialise(self):
        self.model = model.Model(self.name)
        self.model.initialise()

        self.view = view.MainFrame(80,60)
        self.view.initialise(self.model)

        self.model.print()

    def run(self):

        key = libtcod.Key()
        mouse = libtcod.Mouse()

        while not libtcod.console_is_window_closed():

            # Loop to process game events
            event = self.model.get_next_event()
            while event is not None:
                self.view.process_event(event)
                event = self.model.get_next_event()

            libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS, key, mouse)
            action = self.handle_keys(key)

            move = action.get('move')
            exit = action.get('exit')
            fullscreen = action.get('fullscreen')
            stairs = action.get('take stairs')

            if move:
                dx, dy = move
                self.model.move_player(dx,dy)
            elif stairs:
                self.model.take_stairs()

            if exit:
                return True

            if fullscreen:
                libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

            self.view.draw()

    def handle_keys(self, key):

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
            #self.view.add_message("New floor")


        # No key was pressed
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