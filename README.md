# Python Rogue-like Game using TCOD lib
## Overview
This game is a rogue-like game that uses the `libtcod` library and is loosely based on the python rogue-like tutorial.

### Controls
Game Ready
* `N` creat a new character
* `SPACE` to start
* `Esc` quit the game

Create New Character Screen
* `N` change player's name
* `C` change player's class
* `Esc` exit screen

Game Playing
* Arrow keys - move and attack enemy
* `G` get an item
* `U` use item currently equipped in Item slot
* `Z` skip turn
* `C` character screen
* `I` inventory screen
* `Esc` pause game

Inventory Screen
* `E` equip an item
* `U` use and item
* `D` drop and item
* `Esc` exit screen

Character Screen
* Arrow keys - change selected ability
* `L` level-up and increase selected ability
* `Esc` exit screen

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
* "Fog of War" unexplored map and Field of View lighting
* Random enemies in each room that scale as you go deeper
* Random items scattered across the floor with probability governed by game rules
* Potions and Scrolls have randomised effects
* DnD 4e-like classes, abilities and combat rules
* Perma-death
* No game save feature (as yet)

## Package Structure
Overview:
* `roguelike`
    * `model` - modules containing the classes for the game, floors, entities, etc.
    * `view` - modules containing the classes for all of the views
    * `controller` - main control loop
* `tutorial` directory - how I started out following thr python tutorial    

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
<img height=350 width=300 src="https://github.com/kwoolter/roguelike/tree/master/roguelike/view/screenshots/new_character.JPG" alt="new character">
</td>
<td>
<img height=350 width=300 src="https://github.com/kwoolter/roguelike/tree/master/roguelike/view/screenshots/floor1.JPG" alt="exploring">
</td>
</tr>
<tr>
<td>
<img height=350 width=300 src="https://github.com/kwoolter/roguelike/tree/master/roguelike/view/screenshots/inventor.JPG" alt="inventory">
</td>
<td>
<img height=350 width=300 src="https://github.com/kwoolter/roguelike/tree/master/roguelike/view/screenshots/character.JPG" alt="character">
</td>
</tr>
</table>


# Useful Links

## Documentation
* https://libtcod.github.io/docs/index2.html?c=false&cpp=false&cs=false&py=true&lua=false

## Tutorial on writing a game using libtcod
* http://rogueliketutorials.com/tutorials/tcod/

## Fonts that you can load into libtcod
* https://docs.rs/crate/tcod/0.10.0/source/fonts/README.txt
* https://www.gridsagegames.com/rexpaint/resources.html#Fonts

## Libtcod pre-defined colours
* https://libtcod.github.io/docs/html2/color.html?c=false&cpp=false&cs=false&py=true&lua=false
* https://i.imgur.com/taWlWoW.png
