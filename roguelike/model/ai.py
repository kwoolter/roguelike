
import math

class AIBot:

    INSTRUCTION_FAIL_NOP = "NOP"
    INSTRUCTION_FAIL_TICK = "TICK"
    INSTRUCTION_FAIL_SKIP = "SKIP"
    INSTRUCTION_FAIL_VALID_OPTIONS = (INSTRUCTION_FAIL_NOP, INSTRUCTION_FAIL_SKIP, INSTRUCTION_FAIL_TICK)

    def __init__(self, name: str, target_object: Entity, floor: Floor, tick_slow_factor: int = 1):
        self.name = name
        self.target_object = target_object
        self.initial_xy = self.target_object.xy
        self.floor = floor
        self.tick_slow_factor = tick_slow_factor
        self.loop = False
        self.tick_count = 1
        self._debug = False

    def debug(self, debug_on: bool = None):
        if debug_on is None:
            self._debug = not self._debug
        else:
            self._debug = debug_on

    def tick(self):
        self.tick_count += 1

    def reset(self):
        self.tick_count = 0

    def distance_to_target(self, target: Entity):

        fx = self.target_object.rect.centerx
        fy = self.target_object.rect.centery

        tx = target.rect.centerx
        ty = target.rect.centery

        distance = math.sqrt((fx - tx) ** 2 + (fy - ty) ** 2)

        return distance

    def __str__(self):
        text = "Subject:{0} at {1} moved from original position {2}".format(self.target_object.name,
                                                                            str(self.target_object.xyz),
                                                                            str(self.initial_xyz))
        return text



class AIBotTracker(AIBot):

    def __init__(self, target_object: Entity, floor: Floor, tick_slow_factor: int = 1):

        super().__init__(str(__class__), target_object, floor, tick_slow_factor)

        self.following_object = None
        self.navigator = None
        self.failed_ticks = 0
        self.failed_ticks_limit = 10

    def __str__(self):

        text = "{0} Bot: current target:{1} current position:{2}".format(self.name,
                                                                         str(self.following_object),
                                                                         str(self.target_object.xy))

        return text

    def set_instructions(self, new_target: Entity, sight_range: int = 100, loop: bool = True):

        self.following_object = new_target
        self.sight_range = sight_range
        self.loop = loop

    def tick(self):

        success = False

        # If it's not our turn or
        # We haven't got a target
        if super().tick() is False or \
                self.following_object is None:
            return success

        # If we have had too many failed attempts at tracking the object then give-up
        if self.failed_ticks > self.failed_ticks_limit:
            self.failed_ticks = 0
            return success

        # See if we are close enough to the target and
        # Check that there is a direct path to it
        target_in_sight = self.distance_from_target(self.following_object) < self.sight_range

        # If we can see it....
        if target_in_sight is True:

            cx = self.following_object.rect.centerx
            cy = self.following_object.rect.centery

            x = self.target_object.rect.centerx
            y = self.target_object.rect.centery

            # Try and track the target's X position

        if self._debug is True and self.failed_ticks >0:
            print("Failed {0} vs. limit {1}".format(self.failed_ticks, self.failed_ticks_limit   ))

        return success

    def reset(self):
        super().reset()
        self.failed_ticks = 0

from .entity_factory import Entity
from .model import Floor