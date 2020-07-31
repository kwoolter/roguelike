import roguelike.controller as cont

def main():

    c = cont.Controller("Rogue Dungeon")
    c.initialise()
    c.run()

    exit(0)


if __name__ == "__main__":
    main()

