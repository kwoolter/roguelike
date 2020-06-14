import roguelike.model as model
import roguelike.view as view
import tcod as libtcod

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

    def run(self):

        key = libtcod.Key()
        mouse = libtcod.Mouse()

        while not libtcod.console_is_window_closed():

            libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS, key, mouse)
            action = self.handle_keys(key)

            move = action.get('move')
            exit = action.get('exit')
            fullscreen = action.get('fullscreen')

            if move:
                dx, dy = move
                self.model.move_player(dx,dy)

            if exit:
                return True

            if fullscreen:
                libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

            self.view.draw()

    def handle_keys(self, key):
        # Movement keys
        if key.vk == libtcod.KEY_UP:
            return {'move': (0, -1)}
        elif key.vk == libtcod.KEY_DOWN:
            return {'move': (0, 1)}
        elif key.vk == libtcod.KEY_LEFT:
            return {'move': (-1, 0)}
        elif key.vk == libtcod.KEY_RIGHT:
            return {'move': (1, 0)}

        if key.vk == libtcod.KEY_ENTER and key.lalt:
            # Alt+Enter: toggle full screen
            return {'fullscreen': True}

        elif key.vk == libtcod.KEY_ESCAPE:
            # Exit the game
            return {'exit': True}

        # No key was pressed
        return {}
