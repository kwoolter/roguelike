# Python Rogue-like Game using TCOD lib
kwoolter :monkey: :copyright: 2020
## Overview
This game is a rogue-like game that uses the `libtcod` library and is loosely based on the python rogue-like tutorial.

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

## Controls

* `F1` help on controls available from current screen
* `Page Up` and `Page Down` - change font size

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
* `X` examine item on floor
* `Z` skip turn
* `C` character screen
* `R` inventory screen
* `ENTER` or `V` travel down stairs
* `Esc` pause game

Game Paused Screen
* `Q` quit the game
* `Esc` continue playing game

Inventory Screen
* `E` equip an item
* `Q` or `U` use an item
* `X` examine an item
* `F` drop an item
* `Esc` or `R` exit screen

Character Screen
* Arrow keys or `WASD` - change selected ability
* `L`, `E` or `SPACE` level-up and increase selected ability
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

## Background

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
* Random colour palettes and random room and dungeon level names
* Random Lore generation
* DnD-like classes, abilities, monsters and combat rules
* DnD-like armour, weapons and other items
* DnD-like ability checks
* Inventory and Shop features
* Perma-death

# The Game Design

## Package Structure
Overview:
* `roguelike`
    * `model` - modules containing the classes for the game, floors, entities, etc.
    * `view` - modules containing the classes for all of the views
    * `controller` - main control loop
* `tutorial` directory - how I started out following the python tutorial    

### `model` package
* `model.py` - main module that contains `Model`, `Floor`, `Room`, `Tunnel` classes 
* `entity_factory.py` - contains `Entity`, `EntityFactory`, `Player`, `Fighter`, `Inventory` classes
* `combat.py` - contains `CombatEquipment`, `CombatEquipmentFactory`, `CombatClass`, `CombatClassFactory` classes
* `events.py` - all of the event names used in the game
* `themes.py` - module for managing colour themes and random name generation
* `data` directory - data files for the game
    * `entities.csv` - all of the game objects and their properties
    * `combat_equipment.csv`- more properties for entities that are armour or weapons
    * `combat_classes.csv` - the different types of fighter classes and their abilities
    * `game_parameters.csv` - the rules of how the game scales in difficulty
    * `ability_checks.csv` - which items can you perform an ability check on and what are the outcomes for success and failure
    * `themes` directory - data files for colour themes and random name generation
        * `floor_palettes.csv` - colour palettes for different themes
        * `room_palettes.csv` - room colours for different themes
        * `rogue_history.cfg` - config file for name generation using `libtcod.namegen_generate()` functionality 
        * `room_names.csv` - not used anymore as switch to random name generation using `libtcod` library

### `view` package
* `view.py` - main module that contains `MainFrame`, `FloorView` and other UI View related classes
* `view_utils.py` - utility classes for drawing stuff on a console
* `fonts` directory - different font files that can be used with `libtcod`
* `screenshots` directory - screenshots of the game in action

### `controller` package
* `controller.py` - main game loop, keyboard event handling, orchestration of game states and UI states

## Dependencies
* Python 3
* `tcod` - creating and writing to consoles, keyboard events, colours, field of view (FOV) calculations, random name generation, etc.
* `numpy` - floor maps and properties.  Also used by `tcod` library for FOV calculations
* `pandas` - used for loading in `csv` files that hold the game data e.g. entities, combat items, etc.
* `pygame` - only used for the `Rect` class

# How Does The Game's Difficulty Scale?
## Basic Concept
The `Entity` objects that appear in the game have a count and probability metric defined either for the current `Floor` or for each individual `Room` on the `Floor`.  
For example, what is the maximum number of rats that you want to add to a room and what is the probability of each rat successfully being added?  You may want at most 3 rats per room each with a 50% probability.

So in the game, for a given metric `y` you can specify how it is calculated using this formula:

`y = a*x + b + (x//d) * ad`

Where `x` is the dungeon level that you are currently on and a, b, d and ad are parameters defined for each metric.

So breaking this up, `y = a*x + b` is the simple formula for any straight line plotted on an xy axis. `a` represents 
the slope of the line and `b` is the y intercept.  However, you may want an increasing number of rats at lower dungeon 
levels but no rats beyond level 10.  To support this you can add (or subtract) `x` DIV `d` multiplied by a different slope.
So if you want no rats to appear after level 10 you can specific `(x DIV 10) * -100`.

Furthermore, you can constrain `y` by specifying minimum and maximum values.  
This means you can cap the number of rats per room at say 4 but at a minimum always attempt to add 1.

Pulling all of this together you end up with the following lines of code to calculate `y`:

```
        # Calculate y = a*x + b + (x div d)*ad applying min and max constraints
        result = a*xvalue + b
        result += (ad * (xvalue//d))
        result = min(max(result, min_), max_)
```

An example visualisation of this is shown in the graph below where the orange line is `y = ax + b`, 
the blue line is `(x div d) * ad` and the grey line is `y` which is the sum of these two lines with a maximum and minimum applied (4 and 0 respectively).

<img src="https://raw.githubusercontent.com/kwoolter/roguelike/master/roguelike/view/screenshots/graph.JPG">

Using this basic concept you can create interesting **curves** for count and probability for each `Entity` in the game.

## `game_parameters.csv` file
This file defines the count and probability for each entity that you want to appear in the game's rooms or floors.

Columns:
* `Entity` - the name of the entity you want to define a metric for e.g. `Rat`
* `Metric` - which metric are you defining e.g. `Count` or `Probability`?
* `Scope` - what scope is the metric for e.g. `Room` or `Floor`?
* `x` - what is the name of the variable that you want to substitute as `x` into the model - typically `Level`
* `a` - slope
* `b` - y intercept
* `d` - x DIV value
* `ad` - x DIV value slope
* `min` - the minimum value of `y`
* `max` - the maximum value of `y`
* `Template` - use a template instead of a,b,d,ad values

Use templates for when you want to share `Count` or `Probability` curves across multiple types of `Entity`

## `entities.csv` file
Each `Entity` in the game needs to be defined as a row in this file.

Columns:
* `Name` - the short name of the `Entity` used in other property files e.g. `combat_equipment.csv`
* `Description` - a description of the `Entity` used when it is displayed in text messages
* `Char` - the character used to represent the `Entity` on the game `FloorView`
* `Category` - group entities together by category
* `FG` - foreground colour
* `BG` - background colour
* `Zorder` - order of display in descending order i.e. 0 is draw last
* `IsTransparent` - does light shine through it?
* `IsWalkable` - can you walk onto the same tile as it?
* `IsInteractable` - can you interact with it?
* `IsCollectable` - can you pick it up and put it in your inventory?
* `IsStackable` - can you stack many of the same item?
* `IsEquippable` - can you equip it as a weapon or armour?
* `IsCheckable` - can the player perform an ability check on it?
* `IsEnemy` - is it an enemy of the `Player`?
* `Value` - how much is it worth?


## Adding new Entities
The process for adding new types of `Entity` to the game is as follows:-

1. Add a new row to `entities.csv`
2. Add 2 new rows to `game_parameters.csv`; one for generating `Count` and one for `Probability` metrics
3. If the new `Entity`is a piece of `CombatEquipment` then add a new row to `combat_equipment.csv`
4. If you can ability check the `Entity` then add a new row to `ability_checks.csv`

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
