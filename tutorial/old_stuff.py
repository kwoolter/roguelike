def draw_old(self):
    for e in self.floor.entities:
        x, y = e.xy
        libtcod.console_set_default_foreground(self.con, libtcod.yellow)
        libtcod.console_put_char(self.con, x, y, chr(130), libtcod.BKGND_NONE)

    for c in range(0, 255):
        x = c % 50
        y = c // 50
        libtcod.console_put_char(self.con, x, y, chr(c), libtcod.BKGND_NONE)

    y = 5
    for c in range(200, 255):
        libtcod.console_print(self.con, 0, y, f'{c}:{chr(c)}')

        y += 1

    box = ([218, 196, 194, 196, 191],
           [179, 32, 179, 32, 179],
           [195, 196, 197, 196, 180],
           [179, 32, 179, 32, 179],
           [192, 196, 193, 196, 217])
    x = 5
    y = 5
    so = ScreenObject2DArray(box, fg=libtcod.dark_sea, bg=libtcod.grey)
    so.render(self.con, x, y)

    x += 10

    box2 = ([201, 205, 203, 205, 187],
            [186, 32, 186, 32, 186],
            [204, 205, 206, 205, 185],
            [186, 32, 186, 32, 186],
            [200, 205, 202, 205, 188])
    so = ScreenObject2DArray(box2, fg=libtcod.dark_sea, bg=libtcod.grey)
    so.render(self.con, x, y)

    x += 10

    box3 = np.zeros((5, 5))
    box3.fill(int(178))

    so = ScreenObject2DArray(box3, fg=libtcod.dark_sea, bg=libtcod.grey)
    so.render(self.con, x, y)

    x += 10

    box3 = np.zeros((5, 5))
    box3.fill(int(177))

    so = ScreenObject2DArray(box3, fg=libtcod.dark_sea, bg=libtcod.grey)
    so.render(self.con, x, y)

    x += 10
    box3 = np.zeros((5, 5))
    box3.fill(int(176))
    so = ScreenObject2DArray(box3, fg=libtcod.dark_sea, bg=libtcod.grey)
    so.render(self.con, x, y)

    x = 5
    y += 10

    box2 = ([178, 178, 178, 178, 178],
            [178, 32, 32, 32, 178],
            [178, 32, 32, 32, 178],
            [178, 32, 32, 32, 178],
            [178, 178, 178, 178, 178])

    so = ScreenObject2DArray(box2, fg=libtcod.dark_sea, bg=libtcod.grey)
    so.render(self.con, x, y)

    x += 10

    box2 = ([201, 205, 203, 205, 187],
            [186, 224, 186, 224, 186],
            [204, 205, 206, 205, 185],
            [186, 225, 186, 225, 186],
            [200, 205, 202, 205, 188])

    so = ScreenObject2DArray(box2, fg=libtcod.dark_sea, bg=libtcod.grey)
    so.render(self.con, x, y)

    x += 10

    arrows = ([32, 30, 32],
              [17, 18, 16],
              [32, 31, 32])

    so = ScreenObject2DArray(arrows, fg=libtcod.dark_sea, bg=libtcod.grey)
    so.render(self.con, x, y)

    x += 10

    blocks = ([229, 32, 228, 32, 232],
              [32, 32, 32, 32, 32],
              [231, 32, 230, 32, 230],
              [32, 32, 32, 32, 32],
              [231, 32, 228, 32, 226])

    so = ScreenObject2DArray(blocks, fg=libtcod.dark_sea, bg=libtcod.grey)
    so.render(self.con, x, y)

    libtcod.console_set_default_background(self.con, libtcod.white)
    libtcod.console_print(self.con, 10, 40, "Hello World")
    self.con.print_(10, 45, "Test", bg_blend=libtcod.BKGND_ADD)

    o = ScreenObject("K", fg=libtcod.red, bg=libtcod.yellow)
    o.render(self.con, 17, 17)

    s = ScreenString("Hello World", fg=libtcod.red, bg=libtcod.white)
    s.render(self.con, 10, 10)
    s.render(self.con, 10, 12, alignment=libtcod.CENTER)

    bo = ScreenObject2DArray(box2, fg=libtcod.orange, bg=libtcod.yellow)
    bo.render(self.con, 40, 10)

    text_box = ['###', '#O#', '###']
    bo = ScreenObject2DArray(text_box, fg=libtcod.red, bg=libtcod.white)
    bo.render(self.con, 40, 20)

    s = "This is the end. My only friend, the end. I'll never look into your eyes again!"
    sr = ScreenStringRect(text=s, width=10, height=10,
                          fg=libtcod.darkest_blue, bg=libtcod.lightest_lime,
                          alignment=libtcod.CENTER)
    sr.render(self.con, 20, 20)

    libtcod.console_set_default_background(self.con, self.bg)
    libtcod.console_clear(self.con)

    for room in self.floor.map_rooms.values():
        box = np.array([['#' for y in range(room.height + 2)] for x in range(room.width + 2)])
        box[1:-1, 1:-1] = ScreenObject.BLANK_CHAR
        bo = ScreenObject2DArray(box, fg=room.fg, bg=room.bg)
        bo.render(self.con, room.x - 1, room.y - 1)

        # s = ScreenString(room.name, fg = libtcod.red, bg=libtcod.white)
        # s.render(self.con, room.x-1,room.y-2, alignment=libtcod.LEFT)

    for tunnel in self.floor.map_tunnels:
        so = ScreenObjectList(char=ScreenObject.BLANK_CHAR,
                              positions=tunnel.get_segments(),
                              fg=tunnel.fg,
                              bg=tunnel.bg)
        so.render(self.con)