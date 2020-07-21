
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
        GameParameters.parameters.set_index(["Entity", "Metric"], drop=True, inplace=True)

        print(GameParameters.parameters)

    @staticmethod
    def get_parameter(yname : str, ymetric : str, xvalue : float) -> float:
        """

        :param yname: name of the y parameter that we want to calculate
        :param xvalue: value of the x parameter that is the input in y=f(x)
        :return: returns value of y
        """
        assert (yname,ymetric) in GameParameters.parameters.index, f"Can't find '{yname} {ymetric}' in the game parameters!"

        row = GameParameters.parameters.loc[(yname, ymetric)]

        yscope = row["Scope"]
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

        print(f'When {xname}={xvalue} {yname} {ymetric}={result} per {yscope}')

        return result

    @staticmethod
    def get_parameter_input(yname : str, ymetric : str) -> str:

        assert (yname,ymetric) in GameParameters.parameters.index, f"Can't find '{yname} {ymetric}' in the game parameters!"

        row = GameParameters.parameters.loc[(yname, ymetric)]
        return row["x"]

    @staticmethod
    def get_parameter_scope(yname : str, ymetric : str) -> str:

        assert (yname,ymetric) in GameParameters.parameters.index, f"Can't find '{yname} {ymetric}' in the game parameters!"

        row = GameParameters.parameters.loc[(yname, ymetric)]
        return row["Scope"]

    @staticmethod
    def get_parameters_by_scope(scope_value : str) -> str:
        q = f'Scope=="{scope_value}"'
        results = GameParameters.parameters.query(q)
        return results.index


if __name__ == "__main__":
    GameParameters.load("game_parameters.csv")
    GameParameters.parameters.head()

    for yname, ymetric in GameParameters.parameters.index:
        xname = GameParameters.get_parameter_input(yname, ymetric)
        print(f'To calculate {yname} {ymetric} you need {xname}')

    yname="Room"
    ymetric = "Count"
    xname = GameParameters.get_parameter_input(yname, ymetric)
    yscope = GameParameters.get_parameter_scope(yname, ymetric)


    for xvalue in range(5,20):
        yscope = GameParameters.get_parameter_scope(yname, ymetric)
        result = GameParameters.get_parameter(yname=yname, ymetric=ymetric, xvalue=xvalue)

    level = 10
    entities = ["Room", "Orc", "Troll", "Healing Scroll", "Goblin"]
    for yname in entities:
        result = GameParameters.get_parameter(yname=yname, ymetric = "Count", xvalue=level)

    results = GameParameters.get_parameters_by_scope("Room")
    print(results)
    print(list(results))

    results = GameParameters.get_parameters_by_scope("Floor")
    print(results)
    print(list(results))

