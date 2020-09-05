import re
import random

class DnD_Dice:

    def __init__(self, dnd_dice_text:str):
        self.dice_text = dnd_dice_text
        self.num_dice = 0
        self.num_dice_sides = 0
        self.bonus = 0

        self.parse_dice_text(self.dice_text)

    def __str__(self):
        return self.dice_text

    @staticmethod
    def roll_dice_from_text(dice_text)->int:

        return DnD_Dice(dice_text).roll()


    def parse_dice_text(self, dice_text):

        # Define regex for parsing the text
        number_of_dice = re.compile(r'^\d+(?=d)')
        dice_sides = re.compile(r'(?<=\dd)\d+')
        extra_bonus = re.compile(r'(?<=\d\+)\d+$')

        # Use regex to extract the dice info from the text
        r = number_of_dice.search(dice_text)
        assert r is not None, "Can't find number of dice"
        self.num_dice = int(r[0])
        r = dice_sides.search(dice_text)
        assert r is not None, "Can't find number of dice sides"
        self.num_dice_sides = int(r[0])

        # Bonus is optional
        r = extra_bonus.search(dice_text)
        if r is not None:
            self.bonus = int(r[0])
        else:
            self.bonus = 0


    def roll(self):

        # Now time to roll the dice!
        result = 0

        for i in range(self.num_dice):
            result += random.randint(1, self.num_dice_sides)

        result += self.bonus

        return result

if __name__ == "__main__":

    dice_rolls = ["1d6", "1d4+1", "1d20"]

    for dice in dice_rolls:

        d1 = DnD_Dice(dice)
        r = d1.roll()
        print(f'Rolling {d1} dice....result = {r}')


    for dice in dice_rolls:
        r=DnD_Dice.roll_dice_from_text(dice)
        print(f'Rolling {dice} dice....result = {r}')