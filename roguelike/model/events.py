class Event():

    # Event Types
    DEBUG = "debug"
    QUIT = "quit"
    DEFAULT = "default"
    STATE = "state"
    GAME = "game"
    EFFECT = "effect"

    # Define states
    STATE_LOADED = "Game Loaded"
    STATE_READY = "Game Ready"
    STATE_PLAYING = "Game Playing"
    STATE_PAUSED = "Game Paused"
    STATE_GAME_OVER = "Game Over"
    STATE_WORLD_COMPLETE = "Game World Complete"

    # Game events
    GAME_NEW_FLOOR = "new floor"
    GAME_FLOOR_COMPLETED = "floor completed"
    TICK = "Tick"


    # Player action events
    ACTION_FAILED = "action failed"
    ACTION_SUCCEEDED = "action succeeded"
    ACTION_ATTACK = "attack"
    ACTION_EQUIP = "equip"
    ACTION_TAKE_ITEM = "take_item"
    LEVEL_UP_AVAILABLE = "level up available"
    LEVEL_UP = "level up"
    PLAYER_DEAD = "player dead"

    # Event Names
    EFFECT_START = "Effect Start"
    EFFECT_END = "Effect End"
    HELP = "Help"
    COLLIDE = "collide"
    KILL_ENEMY = "kill_enemy"
    INTERACT = "interact"
    READ = "read"
    BLOCKED = "blocked"

    DEAD = "dead"
    SECRET = "secret"
    TREASURE = "treasure"
    DOOR_OPEN = "door opened"
    DOOR_LOCKED = "door locked"
    NEW_WORLD = "new world"
    SWITCH = "switch"
    TREASURE_OPEN = "treasure chest open"
    KEY = "key"
    TELEPORT = "teleport"
    GAIN_HEALTH = "gain health"
    LOSE_HEALTH = "lose health"
    KILLED_OPPONENT = "killed opponent"
    MISSED_OPPONENT = "missed opponent"
    DAMAGE_OPPONENT = "damaged opponent"
    VICTORY = "victory"
    TALK = "talk"
    RANDOM_ENVIRONMENT = "random environment"

    # Effects
    EFFECT_FREEZE_ENEMIES = "**Freeze Enemies**"
    EFFECT_KILL_ENEMIES = "Slay Foes"
    EFFECT_SLOW_ENEMIES = "Slow Enemies"
    EFFECT_INVISIBLE = "**Invisibility**"
    EFFECT_PROTECTION = "**Protection**"
    EFFECT_REVEAL_SECRETS = "**Reveal Secrets**"
    EFFECT_MELEE_ATTACK = "Melee Attack"
    EFFECT_ITEM_DISCOVERY = "***Item Discovery***"

    EFFECT_DURATION = {
        EFFECT_INVISIBLE : 200,
        EFFECT_PROTECTION : 200,
        EFFECT_FREEZE_ENEMIES : 200,
        EFFECT_SLOW_ENEMIES: 200,
        EFFECT_REVEAL_SECRETS : 0,
        EFFECT_KILL_ENEMIES : 200,
        EFFECT_ITEM_DISCOVERY: 1000,
        EFFECT_MELEE_ATTACK : 20
    }

    def __init__(self, name: str, description: str = None, type: str = DEFAULT):
        self.name = name
        self.description = description
        self.type = type

    def __str__(self):
        return "{0}:{1} ({2})".format(self.name, self.description, self.type)