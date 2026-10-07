"""Album art for Volume Gamma: a Minecraft-style pixel scene per track (100x100 canvas, scaled x10 with nearest
neighbour) plus an isometric grass-block front cover, then ID3 tags + embedded art on every mp3 (and the wavs).

    ../.venv/bin/python art.py      -> art/*.png, out/cover.jpg, tags written into out/*.mp3 / *.wav
"""
import io
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ALBUM = Path(__file__).resolve().parent
ART = ALBUM / "art"
OUT = ALBUM / "out"
ART.mkdir(exist_ok=True)
W = 100
SCALE = 10

TRACKS = {
    1: ("spawn_point", "Spawn Point"), 2: ("birch", "Birch"), 3: ("pebble_song", "Pebble Song"),
    4: ("lantern_waltz", "Lantern Waltz"), 5: ("dripstone", "Dripstone"), 6: ("disc_amber", "Disc: amber"),
    7: ("disc_piston", "Disc: piston"), 8: ("kelp_forest", "Kelp Forest"), 9: ("basalt_deltas", "Basalt Deltas"),
    10: ("hearth", "Hearth"), 11: ("void_gate", "Void Gate"), 12: ("long_way_home", "Long Way Home"),
    13: ("lichen_bonus", "Lichen"),
}
ARTIST = "Claude"
ALBUM_NAME = "Volume Gamma"

# ---------------------------------------------------------------- 5x7 pixel font
_F = """A 01110 10001 10001 11111 10001 10001 10001
B 11110 10001 10001 11110 10001 10001 11110
C 01110 10001 10000 10000 10000 10001 01110
D 11110 10001 10001 10001 10001 10001 11110
E 11111 10000 10000 11110 10000 10000 11111
F 11111 10000 10000 11110 10000 10000 10000
G 01110 10001 10000 10111 10001 10001 01111
H 10001 10001 10001 11111 10001 10001 10001
I 01110 00100 00100 00100 00100 00100 01110
J 00111 00010 00010 00010 00010 10010 01100
K 10001 10010 10100 11000 10100 10010 10001
L 10000 10000 10000 10000 10000 10000 11111
M 10001 11011 10101 10101 10001 10001 10001
N 10001 10001 11001 10101 10011 10001 10001
O 01110 10001 10001 10001 10001 10001 01110
P 11110 10001 10001 11110 10000 10000 10000
Q 01110 10001 10001 10001 10101 10010 01101
R 11110 10001 10001 11110 10100 10010 10001
S 01111 10000 10000 01110 00001 00001 11110
T 11111 00100 00100 00100 00100 00100 00100
U 10001 10001 10001 10001 10001 10001 01110
V 10001 10001 10001 10001 10001 01010 00100
W 10001 10001 10001 10101 10101 10101 01010
X 10001 10001 01010 00100 01010 10001 10001
Y 10001 10001 01010 00100 00100 00100 00100
Z 11111 00001 00010 00100 01000 10000 11111
0 01110 10001 10011 10101 11001 10001 01110
1 00100 01100 00100 00100 00100 00100 01110
2 01110 10001 00001 00010 00100 01000 11111
3 11111 00010 00100 00010 00001 10001 01110
4 00010 00110 01010 10010 11111 00010 00010
5 11111 10000 11110 00001 00001 10001 01110
6 00110 01000 10000 11110 10001 10001 01110
7 11111 00001 00010 00100 01000 01000 01000
8 01110 10001 10001 01110 10001 10001 01110
9 01110 10001 10001 01111 00001 00010 01100
: 00000 00100 00100 00000 00100 00100 00000
. 00000 00000 00000 00000 00000 00100 00100"""
FONT = {ln[0]: [r for r in ln[2:].split()] for ln in _F.splitlines()}
FONT[" "] = ["00000"] * 7


def text_w(s):
    return len(s) * 6 - 1


def text(img, s, x, y, col, shadow=(20, 20, 20), scale=1):
    for dx, dy, c in (((scale, scale, shadow),) if shadow else ()) + ((0, 0, col),):
        cx = x + dx
        for ch in s.upper():
            g = FONT.get(ch, FONT[" "])
            for r, row in enumerate(g):
                for k, bit in enumerate(row):
                    if bit == "1":
                        img[y + dy + r * scale:y + dy + (r + 1) * scale, cx + k * scale:cx + (k + 1) * scale] = c
            cx += 6 * scale


# ---------------------------------------------------------------- pixel helpers
class Canvas:
    def __init__(self, seed):
        self.a = np.zeros((W, W, 3), dtype=np.float32)
        self.r = random.Random(seed)
        self.np = np.random.default_rng(seed)

    def put(self, x, y, col, j=0):
        if 0 <= x < W and 0 <= y < W:
            c = np.array(col, dtype=np.float32)
            if j:
                c = c * (1 + self.r.uniform(-j, j) / 100)
            self.a[y, x] = c

    def rect(self, x0, y0, x1, y1, col, j=8):
        for y in range(max(0, y0), min(W, y1)):
            for x in range(max(0, x0), min(W, x1)):
                self.put(x, y, col, j)

    def grad(self, top, bottom, y0=0, y1=W, band=3):
        """Vertical gradient quantised in `band`-pixel steps (banded, like a game sky)."""
        for y in range(y0, y1):
            f = ((y - y0) // band * band) / max(1, y1 - y0 - 1)
            self.a[y, :] = np.array(top) * (1 - f) + np.array(bottom) * f

    def disc(self, cx, cy, r, col, j=0):
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if (x - cx + 0.5) ** 2 + (y - cy + 0.5) ** 2 <= r * r:
                    self.put(x, y, col, j)

    def stars(self, n, ymax, cols=((235, 235, 255), (180, 180, 220))):
        for _ in range(n):
            self.put(self.r.randrange(W), self.r.randrange(ymax), self.r.choice(cols))

    def glow(self, cx, cy, r, col, strength=0.6):
        yy, xx = np.mgrid[0:W, 0:W]
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        g = np.clip(1 - d / r, 0, 1)[..., None] ** 2 * strength
        g = np.round(g * 5) / 5                                   # stepped, pixel-art glow
        self.a = self.a * (1 - g) + np.array(col) * g

    def ground(self, h, grass=(95, 159, 53), dirt=(134, 96, 67), stone=(125, 125, 125), depth=16):
        for x in range(W):
            top = int(h(x))
            for y in range(top, W):
                d = y - top
                col = grass if d < 2 else (dirt if d < depth + (x * 7 % 3) else stone)
                if d == 2 and self.r.random() < 0.4:
                    col = grass
                self.put(x, y, col, 10)

    def title(self, s, num=None, col=(255, 255, 255)):
        y = 86
        self.a[y - 3:y + 10] *= 0.45                             # dark band behind the title
        text(self.a, s, (W - text_w(s)) // 2, y, col, shadow=(25, 25, 25))
        if num is not None:
            text(self.a, f"{num:02d}", 3, 3, (255, 255, 160), shadow=(25, 25, 25))

    def image(self):
        img = Image.fromarray(np.clip(self.a, 0, 255).astype(np.uint8))
        return img.resize((W * SCALE, W * SCALE), Image.NEAREST)


def tree_oak(c, x, base):
    c.rect(x, base - 12, x + 2, base, (102, 81, 50))
    for y in range(base - 20, base - 9):
        for xx in range(x - 6, x + 8):
            if c.r.random() < 0.88 and abs(xx - x - 0.5) + abs(y - (base - 15)) * 0.9 < 9:
                c.put(xx, y, c.r.choice([(58, 112, 37), (72, 133, 44), (48, 96, 30)]))


def clouds(c, n, ymax, col=(250, 250, 250)):
    for _ in range(n):
        x, y = c.r.randrange(-10, W), c.r.randrange(4, ymax)
        w = c.r.randrange(10, 22)
        c.rect(x, y, x + w, y + 3, col, 2)
        c.rect(x + 3, y - 2, x + w - 4, y, col, 2)


# ---------------------------------------------------------------- scenes
def s_spawn(c):
    c.grad((74, 111, 181), (243, 178, 122), 0, 70)
    c.glow(72, 34, 22, (255, 230, 170), 0.5)
    c.rect(66, 28, 78, 40, (255, 242, 190), 2)
    clouds(c, 4, 30)
    c.ground(lambda x: 64 + 4 * math.sin(x / 13) + 2 * math.sin(x / 5 + 1))
    tree_oak(c, 24, int(64 + 4 * math.sin(24 / 13) + 2 * math.sin(24 / 5 + 1)) + 1)


def s_birch(c):
    c.grad((150, 170, 190), (205, 215, 210), 0, 75)
    c.ground(lambda x: 74 + math.sin(x / 9), grass=(110, 150, 70))
    for x in (8, 27, 49, 68, 87):
        top = c.r.randrange(14, 26)
        for y in range(top, 76):
            for k in range(3):
                col = (215, 215, 205) if c.r.random() > 0.18 else (40, 40, 40)
                c.put(x + k, y, col, 4)
        for y in range(top - 14, top + 6):
            for xx in range(x - 7, x + 10):
                if c.r.random() < 0.75 and abs(xx - x - 1) + abs(y - top + 4) < 11:
                    c.put(xx, y, c.r.choice([(128, 167, 85), (110, 150, 70), (150, 185, 100)]))
    for _ in range(12):
        c.put(c.r.randrange(W), c.r.randrange(30, 80), (230, 190, 70))


def s_pebble(c):
    c.grad((110, 165, 255), (170, 210, 255), 0, 60)
    clouds(c, 6, 40)
    c.ground(lambda x: 58 + 2 * math.sin(x / 15), grass=(110, 185, 60), dirt=(96, 160, 52), depth=40)
    for i in range(14):                                         # a pebble path winding toward the viewer
        t = i / 13
        x, y = 50 + 18 * math.sin(t * 3) * t, 60 + 26 * t
        r = 1.2 + 3.2 * t
        c.disc(x, y, r, c.r.choice([(140, 140, 140), (160, 155, 150), (120, 120, 125)]), 8)
    for _ in range(30):
        x, y = c.r.randrange(W), c.r.randrange(62, 84)
        c.put(x, y + 1, (60, 120, 40))
        c.put(x, y, c.r.choice([(230, 60, 50), (250, 220, 60), (240, 240, 240), (120, 150, 250)]))


def s_lantern(c):
    c.grad((10, 14, 40), (35, 45, 90), 0, 80)
    c.stars(70, 70)
    c.rect(76, 10, 86, 20, (230, 230, 210), 3)
    c.rect(76, 10, 80, 20, (60, 70, 110), 3)                    # moon phase
    c.ground(lambda x: 80 + math.sin(x / 11), grass=(40, 70, 40), dirt=(60, 45, 35))
    c.rect(30, 30, 33, 81, (95, 72, 45))                        # fence post + arm
    c.rect(30, 30, 50, 32, (95, 72, 45))
    c.rect(46, 32, 47, 38, (50, 50, 50), 0)                     # chain
    c.glow(46.5, 43, 26, (255, 180, 80), 0.55)
    c.rect(43, 38, 50, 48, (60, 60, 70), 4)
    c.rect(44, 40, 49, 46, (255, 200, 90), 6)
    for _ in range(14):                                         # fireflies
        c.put(c.r.randrange(W), c.r.randrange(40, 80), (220, 255, 120))


def s_dripstone(c):
    c.a[:] = 0
    for y in range(W):
        for x in range(W):
            c.put(x, y, (52, 48, 46), 22)
    for x0 in range(0, W, 7):                                   # stalactites
        h = c.r.randrange(8, 34)
        w = c.r.randrange(2, 5)
        for y in range(h):
            half = w * (1 - y / h)
            for x in range(int(x0 - half), int(x0 + half) + 1):
                c.put(x, y, (132, 102, 82), 12)
        c.put(x0, h + c.r.randrange(4, 20), (120, 200, 255))  # falling drop
    for x0 in range(4, W, 11):                                  # stalagmites
        h = c.r.randrange(6, 20)
        for y in range(h):
            half = 3 * (1 - y / h)
            for x in range(int(x0 - half), int(x0 + half) + 1):
                c.put(x, 80 - y, (122, 95, 78), 12)
    c.rect(0, 80, W, W, (40, 70, 120), 10)                      # still pool
    for x in range(0, W, 3):
        c.put(x, 80, (90, 140, 200))
    c.glow(20, 60, 18, (110, 200, 160), 0.25)                   # glow lichen
    for _ in range(25):
        c.put(c.r.randrange(0, 45), c.r.randrange(45, 80), (130, 230, 170))


def record(c, cx, cy, label, label2):
    for y in range(W):
        for x in range(W):
            d = math.hypot(x - cx + 0.5, y - cy + 0.5)
            if d <= 32:
                g = 22 + (12 if int(d) % 3 == 0 else 0)
                c.put(x, y, (g, g, g + 3), 4)
            if d <= 11:
                c.put(x, y, label, 5)
            if 6 <= d <= 7.2 and x < cx:
                c.put(x, y, label2)
            if d <= 1.6:
                c.put(x, y, (15, 15, 15))
    for k in range(10):                                         # specular streak
        c.put(int(cx - 20 + k), int(cy - 22 + k * 0.9), (110, 110, 115))


def s_amber(c):
    for y in range(W):
        for x in range(W):
            plank = (y // 8) % 2
            col = (110, 74, 44) if plank else (98, 66, 39)
            if y % 8 == 0 or (x + 30 * plank) % 33 == 0:
                col = (70, 46, 28)
            c.put(x, y, col, 7)
    c.glow(50, 44, 40, (255, 190, 90), 0.25)
    record(c, 50, 44, (230, 150, 40), (255, 210, 120))


def s_piston(c):
    for y in range(W):
        for x in range(W):
            brick = ((y // 6) % 2) * 6
            col = (120, 120, 120) if (y % 6 and (x + brick) % 12) else (85, 85, 85)
            c.put(x, y, col, 8)
    for x in range(W):                                          # redstone dust wiring
        c.put(x, 92 - int(4 * abs(math.sin(x / 9))), (200, 20, 20))
    for y in range(80, W):
        c.put(12, y, (200, 20, 20))
    c.rect(6, 6, 20, 18, (170, 130, 80), 6)                     # piston head
    c.rect(11, 18, 15, 26, (110, 110, 110), 4)
    record(c, 52, 44, (60, 200, 80), (200, 250, 120))


def s_kelp(c):
    c.grad((70, 160, 200), (8, 30, 70), 0, W, band=4)
    for k in range(5):                                          # light shafts
        x0 = 10 + k * 22
        for y in range(0, 70):
            x = int(x0 + y * 0.35)
            for d in range(3):
                if 0 <= x + d < W:
                    c.a[y, x + d] = c.a[y, x + d] * 0.85 + np.array([140, 210, 230]) * 0.15
    c.ground(lambda x: 88 + 2 * math.sin(x / 7), grass=(200, 190, 130), dirt=(180, 170, 115), stone=(150, 140, 100))
    for x0 in (8, 17, 31, 44, 60, 71, 83, 93):
        h = c.r.randrange(35, 70)
        for y in range(h):
            x = int(x0 + 2 * math.sin(y / 6 + x0))
            yy = 88 - y
            c.put(x, yy, (50, 120, 40), 15)
            c.put(x + 1, yy, (40, 100, 35), 15)
            if y % 7 == 3:
                c.put(x + 2, yy, (90, 160, 50))
    for _ in range(26):
        x, y = c.r.randrange(W), c.r.randrange(5, 85)
        c.put(x, y, (200, 240, 255))
        if c.r.random() < 0.4:
            c.put(x + 1, y - 2, (170, 220, 245))
    for fx, fy in ((62, 34), (24, 52)):                         # fish
        c.rect(fx, fy, fx + 5, fy + 3, (240, 140, 50), 5)
        c.put(fx - 1, fy + 1, (240, 140, 50))
        c.put(fx + 4, fy + 1, (20, 20, 20))


def s_basalt(c):
    c.grad((60, 45, 60), (140, 90, 90), 0, W, band=4)
    for x0 in range(-2, W, 9):                                  # basalt columns
        h = c.r.randrange(30, 75)
        w = c.r.randrange(6, 9)
        for y in range(W - h, W):
            for x in range(x0, x0 + w):
                col = (75, 75, 80) if (x - x0) % 3 else (55, 55, 60)
                c.put(x, y, col, 10)
        c.rect(x0, W - h, x0 + w, W - h + 1, (110, 110, 118), 5)
    for _ in range(4):                                          # lava seams
        x0, y0 = c.r.randrange(W), c.r.randrange(70, 95)
        c.glow(x0, y0, 10, (255, 120, 20), 0.5)
        c.rect(x0 - 4, y0, x0 + 4, y0 + 2, (255, 150, 30), 10)
    for _ in range(60):                                         # ash
        c.put(c.r.randrange(W), c.r.randrange(W), c.r.choice([(200, 200, 200), (140, 140, 140)]))


def s_hearth(c):
    c.grad((80, 70, 140), (250, 150, 100), 0, 70)
    clouds(c, 3, 25, col=(255, 190, 170))
    c.ground(lambda x: 72 + math.sin(x / 10))
    c.rect(30, 50, 66, 73, (162, 130, 78), 8)                   # oak plank walls
    for y in range(50, 73, 4):
        c.rect(30, y, 66, y + 1, (130, 100, 60), 3)
    c.rect(30, 70, 66, 73, (120, 120, 120), 14)                 # cobble base
    for k in range(14):                                         # roof
        c.rect(26 + k, 50 - k, 70 - k, 51 - k, (90, 60, 40), 8)
    c.glow(42, 59, 16, (255, 200, 90), 0.45)
    c.rect(38, 55, 46, 63, (255, 210, 110), 6)
    c.rect(41, 55, 42, 63, (90, 60, 40))
    c.rect(52, 58, 58, 73, (100, 70, 40), 6)                    # door
    c.rect(58, 32, 62, 46, (120, 120, 120), 12)                 # chimney + smoke
    for k in range(6):
        c.rect(58 + k * 2, 28 - k * 5, 62 + k * 2, 31 - k * 5, (200, 195, 200), 6)
    tree_oak(c, 82, 73)


def s_void(c):
    c.grad((8, 0, 15), (30, 10, 40), 0, W)
    c.stars(110, W, cols=((230, 200, 255), (160, 120, 200), (255, 255, 255)))
    for x in range(10, 90):                                     # floating end-stone island
        top = 70 + int(2 * math.sin(x / 6))
        depth = int(14 * math.sqrt(max(0, 1 - ((x - 50) / 40) ** 2))) + c.r.randrange(0, 3)
        for y in range(top, top + depth):
            c.put(x, y, (219, 222, 158), 8)
    for x0, h in ((22, 38), (44, 52), (68, 44)):                # obsidian pillars with crystals
        c.rect(x0, 70 - h, x0 + 6, 71, (25, 15, 40), 25)
        c.glow(x0 + 3, 66 - h, 8, (255, 120, 220), 0.55)
        c.rect(x0 + 1, 63 - h, x0 + 5, 69 - h, (255, 160, 230), 8)
    c.rect(46, 58, 54, 62, (30, 60, 50), 5)                     # portal frame
    c.rect(47, 59, 53, 61, (10, 10, 25), 5)
    for _ in range(30):
        c.put(c.r.randrange(W), c.r.randrange(W), (170, 60, 220))


def s_home(c):
    c.grad((60, 40, 100), (250, 140, 70), 0, 58, band=3)
    c.rect(38, 46, 62, 58, (255, 200, 110), 3)                  # setting sun
    for y in range(58, W):                                      # ocean with sun reflection
        for x in range(W):
            col = (40, 60, 110)
            if 40 < x < 60 and (y + x) % 4 == 0 and c.r.random() < 0.7:
                col = (250, 180, 100)
            c.put(x, y, col, 8)
    c.ground(lambda x: 74 + 0.005 * x * x if x < 76 else W, grass=(70, 120, 45))
    for k in range(18):                                         # path
        t = k / 17
        x = int(4 + 30 * t)
        y = int(74 + 0.005 * (x + 2) ** 2) + 1
        c.rect(x, y, x + 4, y + 2, (150, 120, 80), 6)
    c.rect(34, 71, 36, 76, (60, 110, 170), 0)                   # a tiny walker, heading home
    c.rect(34, 69, 36, 71, (200, 150, 110), 0)
    c.rect(34, 76, 36, 79, (40, 40, 80), 0)


def s_lichen(c):
    for y in range(W):
        for x in range(W):
            cell = ((x // 7 + (y // 6) * 3) * 37) % 5
            col = [(120, 120, 120), (105, 105, 105), (135, 135, 135), (95, 95, 98), (115, 112, 108)][cell]
            if x % 7 == 0 or y % 6 == 0:
                col = (70, 70, 72)
            c.put(x, y, col, 10)
    for _ in range(14):                                         # lichen / moss patches
        cx, cy = c.r.randrange(W), c.r.randrange(80)
        for _ in range(60):
            x, y = int(cx + c.np.normal(0, 4)), int(cy + c.np.normal(0, 3))
            c.put(x, y, c.r.choice([(110, 140, 70), (160, 175, 110), (90, 120, 60), (190, 190, 140)]), 6)
    c.put(70, 60, (240, 240, 120))
    c.put(70, 61, (70, 120, 40))


SCENES = {1: s_spawn, 2: s_birch, 3: s_pebble, 4: s_lantern, 5: s_dripstone, 6: s_amber, 7: s_piston,
          8: s_kelp, 9: s_basalt, 10: s_hearth, 11: s_void, 12: s_home, 13: s_lichen}


# ---------------------------------------------------------------- front cover: isometric grass block
def cover():
    S = W * SCALE
    c = Canvas(42)
    c.grad((120, 170, 240), (200, 225, 250), 0, W, band=4)
    clouds(c, 5, 30)
    text(c.a, "VOLUME GAMMA", (W - text_w("VOLUME GAMMA")) // 2, 8, (255, 255, 255), shadow=(50, 60, 90))
    text(c.a, "CLAUDE", (W - text_w("CLAUDE")) // 2, 87, (250, 250, 230), shadow=(50, 60, 90))
    img = c.image()
    d = ImageDraw.Draw(img)
    r = random.Random(7)
    cx, cy, a = S // 2, 215, 300                                # cube top vertex, edge length (px)
    n = 16

    def P(u, v, w):                                             # iso projection of cube coords (0..1)
        return (cx + (u - v) * a * 0.866, cy + (u + v) * a * 0.5 + w * a)

    grass = [(95, 159, 53), (110, 175, 60), (84, 140, 46), (120, 185, 70)]
    dirt = [(134, 96, 67), (121, 85, 58), (150, 108, 75), (110, 78, 52)]
    for i in range(n):
        for j in range(n):
            u0, u1, v0, v1 = i / n, (i + 1) / n, j / n, (j + 1) / n
            d.polygon([P(u0, v0, 0), P(u1, v0, 0), P(u1, v1, 0), P(u0, v1, 0)], fill=r.choice(grass))
    fringe = [r.randint(2, 4) for _ in range(n)]
    for face, shade in (("left", 0.78), ("right", 0.6)):
        for i in range(n):
            for k in range(n):
                t0, t1, w0, w1 = i / n, (i + 1) / n, k / n, (k + 1) / n
                col = r.choice(grass if k < fringe[i] else dirt)
                col = tuple(int(x * shade) for x in col)
                if face == "left":                              # v = 1 face
                    pts = [P(t0, 1, w0), P(t1, 1, w0), P(t1, 1, w1), P(t0, 1, w1)]
                else:                                           # u = 1 face
                    pts = [P(1, t0, w0), P(1, t1, w0), P(1, t1, w1), P(1, t0, w1)]
                d.polygon(pts, fill=col)
    return img


# ---------------------------------------------------------------- build + tag
def build():
    imgs = {}
    for k, (slug, title) in TRACKS.items():
        c = Canvas(1000 + k)
        SCENES[k](c)
        c.title(title, k)
        img = c.image()
        img.save(ART / f"{k:02d}_{slug}.png")
        imgs[k] = img
    cov = cover()
    cov.save(ART / "cover.png")
    cov.convert("RGB").save(OUT / "cover.jpg", quality=92)      # folder art for players that read cover.jpg
    sheet = Image.new("RGB", (5 * 300, 3 * 300))
    for i, im in enumerate([cov] + [imgs[k] for k in sorted(imgs)]):
        sheet.paste(im.resize((300, 300), Image.NEAREST), ((i % 5) * 300, (i // 5) * 300))
    sheet.save(ART / "contact_sheet.png")
    return cov, imgs


def jpg(img):
    b = io.BytesIO()
    img.convert("RGB").save(b, "JPEG", quality=92)
    return b.getvalue()


def tag(path, title, num, img, total=len(TRACKS)):
    from mutagen.id3 import ID3, APIC, TIT2, TPE1, TPE2, TALB, TRCK, TDRC, TCON, COMM, ID3NoHeaderError
    from mutagen.wave import WAVE
    frames = [TIT2(encoding=3, text=title), TPE1(encoding=3, text=ARTIST), TPE2(encoding=3, text=ARTIST),
              TALB(encoding=3, text=ALBUM_NAME), TDRC(encoding=3, text="2026"), TCON(encoding=3, text="Ambient"),
              COMM(encoding=3, lang="eng", desc="", text="Original music in the manner of C418's Minecraft soundtrack"),
              APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=jpg(img))]
    if num:
        frames.append(TRCK(encoding=3, text=f"{num}/{total}"))
    if path.suffix == ".wav":
        w = WAVE(path)
        if w.tags is None:
            w.add_tags()
        w.tags.clear()
        for f in frames:
            w.tags.add(f)
        w.save()
        return
    try:
        t = ID3(path)
    except ID3NoHeaderError:
        t = ID3()
    t.clear()
    for f in frames:
        t.add(f)
    t.save(path, v2_version=3)


if __name__ == "__main__":
    cov, imgs = build()
    for k, (slug, title) in TRACKS.items():
        for ext in (".mp3", ".wav"):
            p = OUT / f"{k:02d}_{slug}{ext}"
            if p.exists():
                tag(p, title, k, imgs[k])
                print("tagged", p.name)
    for ext in (".mp3", ".wav"):
        p = OUT / f"Volume_Gamma{ext}"
        if p.exists():
            tag(p, "Volume Gamma (full album)", None, cov)
            print("tagged", p.name)
