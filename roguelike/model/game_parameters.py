
from pathlib import Path
import pandas as pd


class GameParameters:
    parameters = None

    def __init__(self):
        pass

    @staticmethod
    def load(file_name: str):

        # Create path for the file that we are going to load
        data_folder = Path(__file__).resolve().parent
        file_to_open = data_folder / "data" / file_name

        # Read in the csv file
        GameParameters.parameters = pd.read_csv(file_to_open)
        GameParameters.parameters.set_index("y", drop=True, inplace=True)
        # self.entities.set_index(self.entities.columns[0], drop=True, inplace=True)

        print(GameParameters.parameters)

    @staticmethod
    def get_parameter(yname : str, xvalue : float) -> float:
        """

        :param yname: name of the y parameter that we want to calculate
        :param xvalue: value of the x parameter that is the input in y=f(x)
        :return: returns value of y
        """
        assert yname in GameParameters.parameters.index, f"Can't find '{yname}' in the game parameters!"

        row = GameParameters.parameters.loc[yname]

        xname = row["x"]
        a = row["a"]
        b = row["b"]
        d = row["d"]
        ad = row["ad"]
        min_ = row["min"]
        max_ = row["max"]

        # Calculate y = a*x + b + (x div d)*ad applying min and max constraints
        result = a*xvalue + b
        result += (ad * xvalue//d)
        result = min(max(result, min_), max_)

        print(f'When {xname}={xvalue} {yname}={result}')

        return result

    @staticmethod
    def get_parameter_input(yname : str) -> str:
        row = GameParameters.parameters.loc[yname]
        return row["x"]


if __name__ == "__main__":
    GameParameters.load("game_parameters.csv")
    GameParameters.parameters.head()

    for yname in GameParameters.parameters.index:
        xname = GameParameters.get_parameter_input(yname)
        print(f'To calculate {yname} you need {xname}')

    yname="Pillar Count"
    xname = GameParameters.get_parameter_input(yname)

    for xvalue in range(5,20):
        result = GameParameters.get_parameter(yname=yname, xvalue=xvalue)
        #print(f'When {xname}={xvalue} {yname}={result}')

    level = 10
    entities = ["Pillar", "Orc", "Troll"]
    for e in entities:
        yname = f'{e} Count'
        result = GameParameters.get_parameter(yname=yname, xvalue=level)
