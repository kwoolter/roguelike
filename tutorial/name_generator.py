import tcod as libtcod
import os


"""
 * RULES:
 * These denote how a word is generated. A rule is a string consisting of
 * normal characters [a-z,A-Z,',-], special characters preceded by a slash (see
 * the notes concerning syllables), underscores to denote spaces and wildcards.
 * Wildcards are preceded by a dollar sign. Here's the full list:
 * "$P" - a random Pre syllable
 * "$s" - a random Start syllable
 * "$m" - a random Middle syllable
 * "$e" - a random End syllable
 * "$p" - a random Post syllable
 * "$v" - a random vocal
 * "$c" - a random consonant
 * "$?" - a random phoneme
 * So, if we hav the following data:
 *   syllablesStart = "Ivan"
 *   syllablesEnd = "Terrible"
 *   rules = "$s_the_$e"
 * the generator will output "Ivan the Terrible".
"""

#############################################
# name generator sample
#############################################


def get_data(path: str) -> str:
    """Return the path to a resource in the libtcod data directory,"""
    SCRIPT_DIR = os.path.dirname(__file__)
    DATA_DIR = os.path.join(SCRIPT_DIR, "data")
    return os.path.join(DATA_DIR, path)


def render_name():

    # parse all *.cfg files in data/namegen
    for file in os.listdir(get_data('namegen')) :
        if file.find('.cfg') > 0 :
            libtcod.namegen_parse(get_data(os.path.join('namegen',file)))
    # get the sets list
    ng_sets=libtcod.namegen_get_sets()
    test_sets = ("Rogue Dungeon Rooms", "Rogue Names")

    for test_set in test_sets:
        print ("=" * 40)
        print(test_set)
        print ("=" * 40)
        for i in range(20):
            ng_names = libtcod.namegen_generate(test_set)
            print(ng_names)

    assert False

    for ng_set in ng_sets:
        print("="*40)
        print(f"{ng_set}")
        print("=" * 40)
        for i in range(10):
            ng_names = libtcod.namegen_generate(ng_set)
            print(ng_names)


if __name__ == "__main__":
    render_name()