# Python Rogue-like using TCOD lib
## Overview
This game is a rogue-like game that uses the `libtcod` library and is loosely based on the python rogue-like tutorial.

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
TBC


## Package Structure

* `roguelike`
    * `model`
    * `view`
    * `controller`


## Dependencies
* Python 3
* `tcod` - creating and writing to consoles, keyboard events, colours, field of view (FOV) calculations, etc.
* `numpy` - floor maps and properties.  Also used by `tcod` library for FOV calculations
* `pandas` - used for loading in `csv` files that hold the game data e.g. entities, combat items, etc.
* `pygame` - only used for the `Rect` class

## Screenshots
TBC


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
