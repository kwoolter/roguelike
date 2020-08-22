# Python Rogue-like Game using TCOD lib
kwoolter :monkey: :copyright: 2020
## Overview
This game is a rogue-like game that uses the `libtcod` library and is loosely based on the python rogue-like tutorial.

### Controls

* `F1` help on controls available from current screen

Game Ready Screen
* `N` create a new character
* `ENTER` or `SPACE` to start the game
* `Esc` quit the game

Create New Character Screen
* `N` change player's name
* `C` change player's class
* `ENTER` or `SPACE` confirm class selection
* `Esc` exit screen

Game Playing Screen
* Arrow keys - move and attack enemy
* `G` or `SPACE` get an item
* `Q` or `U` use item currently equipped in Item slot
* `Z` skip turn
* `C` character screen
* `R` inventory screen
* `ENTER` or `X` travel down stairs
* `Esc` pause game

Game Paused Screen
* `Q` quit the game
* `Esc` continue playing game

Inventory Screen
* `E` equip an item
* `Q` or `U` use an item
* `F` drop an item
* `Esc` or `R` exit screen

Character Screen
* Arrow keys or `WASD` - change selected ability
* `L` or `E` level-up and increase selected ability
* `Esc` exit screen

Shop Screen
* `E` or `B` switch to Buy tab
* `Q` or `V` switch to Sell tab
* Up and down arrow keys or `W` and `S`- change selected item 
* `ENTER` or `SPACE` buy/sell the selected item
* Left and Right arrow keys or `A` and `D` - change item category in Buy tab
* `Esc` exit screen

Game Over Screen
* `ENTER` - continue to Game Ready Screen 

### What is a rogue-like game?

* https://en.wikipedia.org/wiki/Roguelike

### What is the `libtcod` library?

* https://github.com/libtcod/libtcod
* https://libtcod.github.io/docs/

### What is the Python rogue-like tutorial? 

* http://rogueliketutorials.com/about/
* http://rogueliketutorials.com
* http://rogueliketutorials.com/tutorials/tcod/v2/

### What is this game again?????
Features:
* Random dungeon floor generation with more rooms per floor as you get deeper
* Field of View (FoV) lighting
* "Fog of War" unexplored map 
* Random enemies in each room that scale as you go deeper
* Random items scattered across the floor with probability governed by game rules
* Potions and Scrolls have randomised effects
* DnD-like classes, abilities, monsters and combat rules
* DnD-like armour, weapons and other items
* DnD-like ability checks
* Inventory and Shop features
* Perma-death

## Package Structure
Overview:
* `roguelike`
    * `model` - modules containing the classes for the game, floors, entities, etc.
    * `view` - modules containing the classes for all of the views
    * `controller` - main control loop
* `tutorial` directory - how I started out following the python tutorial    

### `model` package
* `model.py` - main module that contains `Model`, `Floor`, `Room`, `Tunnel` classes 
* `entity_factory.py`
* `combat.py`
* `events.py`
* `data` directory - data files for the game
    * `entities.csv` - all of the game objects and their properties
    * `combat_equipment.csv`- more properties for entities that are armour of weapons
    * `combat_classes.csv` - the different types of fighter classes and their abilities
    * `game_parameters.csv` - the rules of how the game scales in difficulty

### `view` package
* `view.py` - main module that contains `MainFrame`, `FloorView` and other UI View related classes
* `view_utils.py` - utility classes for drawing stuff on a console
* `fonts` directory - different font files that can be used with `libtcod`
* `screenshots` directory - screenshots of the game in action

### `controller` package
* `controller.py` - main game loop, keyboard event handling, orchestration of game states and UI states

## Dependencies
* Python 3
* `tcod` - creating and writing to consoles, keyboard events, colours, field of view (FOV) calculations, etc.
* `numpy` - floor maps and properties.  Also used by `tcod` library for FOV calculations
* `pandas` - used for loading in `csv` files that hold the game data e.g. entities, combat items, etc.
* `pygame` - only used for the `Rect` class

## Screenshots

<table>
<tr>
<td>
<img height=325 width=250 src="https://raw.githubusercontent.com/kwoolter/roguelike/master/roguelike/view/screenshots/new_character2.JPG" alt="new character">
</td>
<td>
<img height=325 width=250 src="https://raw.githubusercontent.com/kwoolter/roguelike/master/roguelike/view/screenshots/floor1.JPG" alt="exploring">
</td>
</tr>
<tr>
<td>
<img height=325 width=250 src="https://raw.githubusercontent.com/kwoolter/roguelike/master/roguelike/view/screenshots/inventory2.JPG" alt="inventory">
</td>
<td>
<img height=325 width=250 src="https://raw.githubusercontent.com/kwoolter/roguelike/master/roguelike/view/screenshots/shop2.JPG" alt="character">
</td>
</tr>
</table>

# How Does The Game's Difficulty Scale?
## Basic concept
The `Entity` objects that appear in the game have a count and probability metric defined either for the current `Floor` or for each individual `Room` on the `Floor`.  
For example, what is the maximum number of rats that you want to add to a room and what is the probability of a each rate successfully being added?  You may want at most 3 rats per room each with a 50% probability.

So in the game, for a given metric `y` you can specify how it is calculated using this formula:

`y = a*x + b + (x//d) * ad`

Where `x` is the dungeon level that you are currently on and a, b, d and ad are parameters defined for each metric.

So breaking this up, `y = a*x + b` is the simple formula for any straight line plotted on an xy axis. `a` represents 
the slope of the line and `b` is the y intercept.  However, you may want an increasing number of rats at lower dungeon 
levels but no rats beyond level 10.  To support this you can add (or subtract) `x` DIV `d` multiplied by a different slope.
So if you want no rats to appear after level 10 you can specific `(x DIV 10) * -100`.

Furthermore, you can constraint `y` by specifying minimum and maximum values.  
This means you can cap the number of rats per room at say 4 but at a minimum always attempt to add 1.

Pulling all of this together you end up with the following lines of code to calculate `y`:

```
        # Calculate y = a*x + b + (x div d)*ad applying min and max constraints
        result = a*xvalue + b
        result += (ad * (xvalue//d))
        result = min(max(result, min_), max_)
```

An example visualisation of this is shown in the graph below where the orange line is `y = ax + b`, 
the blue line is `(x div d) * ad` and the grey line is the sum of these two lines with a maximum and minimum applied (4 and 0 respectively).

<img src="https://raw.githubusercontent.com/kwoolter/roguelike/master/roguelike/view/screenshots/graphy.JPG">

Using this basic concept you can create interesting curves for count and probability for each `Entity` in the game.

## `game_parameters.csv` file
This file defines the count and probability for each entity that you want to appear in the game.

Columns:
* `Entity` - the name of the entity you want to define a metric for
* `Metric` - which metric are you defining e.g. Count, Probability
* `Scope` - what scope if the metric for e.g. Room or Floor?
* `x` - what is the name of the variable that you want to substitue as `x` into the model?
* `a` - slope
* `b` - y intercept
* `d` - x modulo value
* `ad` - x modulo value slope
* min - the minimum value of `y`
* max - the maximum value of `y`
* Template - use a template instead of a,b,d,ad values

# Useful Links

## `libtcod` Documentation
* https://libtcod.github.io/docs/index2.html?c=false&cpp=false&cs=false&py=true&lua=false

## Tutorial on writing a game using `libtcod`
* http://rogueliketutorials.com/tutorials/tcod/

## Fonts that you can load into `libtcod`
* https://docs.rs/crate/tcod/0.10.0/source/fonts/README.txt
* https://www.gridsagegames.com/rexpaint/resources.html#Fonts

## `libtcod` pre-defined colours
* https://libtcod.github.io/docs/html2/color.html?c=false&cpp=false&cs=false&py=true&lua=false
* https://i.imgur.com/taWlWoW.png
