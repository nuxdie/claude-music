"""YouTube videos for Volume Gamma: an animated 16:9 pixel scene per track (192x108 canvas, scaled x10 to 1920x1080
with nearest-neighbour), partly driven by the music (loudness envelope, low-end onsets), title card at the start,
small persistent label. Plus a full-album video with chapter timestamps.

    ../.venv/bin/python video.py              # all tracks (parallel) + album video
    ../.venv/bin/python video.py 5 7          # only these tracks (no album video)
    ../.venv/bin/python video.py --still 5    # write video/stills/05_*.png at a few times (quick look)
"""
import math
import random
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import soundfile as sf

from art import TRACKS, FONT, text, text_w, ALBUM_NAME

ALBUM = Path(__file__).resolve().parent
OUT = ALBUM / "out"
VID = ALBUM / "video"
VID.mkdir(exist_ok=True)
W, H = 192, 108
SCALE = 10
FPS = 24
GAP = 2.5                       # same gap as assemble.py


# ---------------------------------------------------------------- drawing primitives on (H, W, 3) float arrays
def put(a, x, y, col, alpha=1.0):
    x, y = int(x), int(y)
    if 0 <= x < W and 0 <= y < H:
        a[y, x] = a[y, x] * (1 - alpha) + np.asarray(col, dtype=np.float32) * alpha


def rect(a, x0, y0, x1, y1, col, alpha=1.0):
    x0, y0, x1, y1 = max(0, int(x0)), max(0, int(y0)), min(W, int(x1)), min(H, int(y1))
    if x1 > x0 and y1 > y0:
        a[y0:y1, x0:x1] = a[y0:y1, x0:x1] * (1 - alpha) + np.asarray(col, dtype=np.float32) * alpha


YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)


def glow(a, cx, cy, r, col, strength=0.6, steps=5):
    d = np.sqrt((XX - cx) ** 2 + (YY - cy) ** 2)
    g = np.clip(1 - d / r, 0, 1) ** 2 * strength
    g = (np.round(g * steps) / steps)[..., None]
    a *= (1 - g)
    a += np.asarray(col, dtype=np.float32) * g


def grad(a, top, bottom, y0=0, y1=H, band=3):
    for y in range(y0, y1):
        f = ((y - y0) // band * band) / max(1, y1 - y0 - 1)
        a[y, :] = np.asarray(top, dtype=np.float32) * (1 - f) + np.asarray(bottom, dtype=np.float32) * f


def mix(c1, c2, f):
    return tuple(np.asarray(c1, dtype=np.float32) * (1 - f) + np.asarray(c2, dtype=np.float32) * f)


class Layer:
    """Static drawing surface with coverage mask (for foregrounds that animated things pass behind)."""

    def __init__(self, seed):
        self.a = np.zeros((H, W, 3), dtype=np.float32)
        self.m = np.zeros((H, W), dtype=bool)
        self.r = random.Random(seed)
        self.np = np.random.default_rng(seed)

    def put(self, x, y, col, j=0):
        x, y = int(x), int(y)
        if 0 <= x < W and 0 <= y < H:
            c = np.asarray(col, dtype=np.float32)
            if j:
                c = c * (1 + self.r.uniform(-j, j) / 100)
            self.a[y, x] = c
            self.m[y, x] = True

    def rect(self, x0, y0, x1, y1, col, j=8):
        for y in range(max(0, int(y0)), min(H, int(y1))):
            for x in range(max(0, int(x0)), min(W, int(x1))):
                self.put(x, y, col, j)

    def disc(self, cx, cy, r, col, j=0):
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if (x - cx + 0.5) ** 2 + (y - cy + 0.5) ** 2 <= r * r:
                    self.put(x, y, col, j)

    def ground(self, h, grass=(95, 159, 53), dirt=(134, 96, 67), stone=(125, 125, 125), depth=16):
        for x in range(W):
            top = int(h(x))
            for y in range(max(0, top), H):
                d = y - top
                col = grass if d < 2 else (dirt if d < depth + (x * 7 % 3) else stone)
                if d == 2 and self.r.random() < 0.4:
                    col = grass
                self.put(x, y, col, 10)

    def tree(self, x, base, leaves=((58, 112, 37), (72, 133, 44), (48, 96, 30)), trunk=(102, 81, 50), size=1.0):
        th = int(12 * size)
        self.rect(x, base - th, x + 2, base, trunk, 6)
        cy = base - th - int(3 * size)
        for y in range(cy - int(8 * size), cy + int(4 * size)):
            for xx in range(x - int(7 * size), x + int(9 * size)):
                if self.r.random() < 0.88 and abs(xx - x - 0.5) + abs(y - cy) * 0.9 < 9 * size:
                    self.put(xx, y, self.r.choice(leaves))


# ---------------------------------------------------------------- particles: stateless functions of time
def particles(seed, n, period):
    """n particles, each with its own phase/position seeds; particle i is reborn every `period` seconds."""
    r = random.Random(seed)
    return [(r.random(), r.random(), r.random(), r.random()) for _ in range(n)], period


def cloud_sprite(seed, w):
    r = random.Random(seed)
    pts = []
    for x in range(w):
        pts.append((x, 0))
        pts.append((x, 1))
        if 2 <= x < w - 3 and r.random() < 0.85:
            pts.append((x, -1))
        if 4 <= x < w - 6 and r.random() < 0.5:
            pts.append((x, -2))
    return pts


def draw_clouds(a, t, seed, n, ymax, speed=0.6, col=(250, 250, 250), alpha=0.95):
    r = random.Random(seed)
    for i in range(n):
        w = r.randrange(12, 28)
        y = r.randrange(6, ymax)
        x0 = r.random() * (W + 40)
        v = speed * (0.6 + 0.8 * r.random())
        x = (x0 + v * t) % (W + 40) - 30
        for dx, dy in cloud_sprite(seed * 100 + i, w):
            put(a, x + dx, y + dy, col, alpha)


NOTE = ["..##.", "..#.#", "..#..", "###..", "###.."]


def draw_note(a, x, y, col, alpha=1.0):
    for r, row in enumerate(NOTE):
        for k, ch in enumerate(row):
            if ch == "#":
                put(a, x + k, y + r, col, alpha)


def hue(h):
    h = h % 1.0
    k = np.array([5, 3, 1]) + h * 6
    v = 1 - np.maximum(0, np.minimum(np.minimum(k % 6, 4 - k % 6), 1))
    return tuple(60 + 195 * v)


# ---------------------------------------------------------------- scenes
class Scene:
    """bg(): static sky layer. fg(): static Layer drawn over 'behind' animation. behind/front(a, t, lv, T)."""
    seed = 0

    def __init__(self, T, env, onsets):
        self.T, self.env, self.onsets = T, env, onsets
        self.r = random.Random(self.seed)
        self.sky = np.zeros((H, W, 3), dtype=np.float32)
        self.L = Layer(self.seed + 1)
        self.bg()
        self.fg()

    def bg(self):
        pass

    def fg(self):
        pass

    def behind(self, a, t, lv):
        pass

    def front(self, a, t, lv):
        pass

    def sky_at(self, t):
        return self.sky.copy()

    def frame(self, t, lv):
        a = self.sky_at(t)
        self.behind(a, t, lv)
        a[self.L.m] = self.L.a[self.L.m]
        self.front(a, t, lv)
        return a


def hills(x, base, amp=5, seed=0):
    return base + amp * math.sin(x / 17 + seed) + 0.4 * amp * math.sin(x / 6 + 1 + seed)


class Spawn(Scene):
    """Sunrise over spawn: the sun climbs and the sky brightens over the whole track; clouds drift; birds."""
    seed = 11

    def fg(self):
        self.L.ground(lambda x: hills(x, 80, 5))
        for x, s in ((40, 1.1), (128, 0.9), (165, 1.0)):
            self.L.tree(x, int(hills(x, 80, 5)) + 1, size=s)

    def sky_at(self, t):
        p = min(1.0, t / self.T)
        a = np.zeros((H, W, 3), dtype=np.float32)
        grad(a, mix((30, 40, 90), (90, 140, 230), p), mix((240, 150, 100), (200, 225, 250), p), 0, 90)
        sy = 78 - 50 * (1 - (1 - p) ** 2)
        glow(a, 140, sy + 6, 34, (255, 225, 160), 0.45 * (1 - 0.5 * p))
        rect(a, 134, sy, 146, sy + 12, (255, 242, 190))
        return a

    def behind(self, a, t, lv):
        draw_clouds(a, t, 3, 7, 40, speed=0.7)

    def front(self, a, t, lv):
        for i in range(3):                                         # a little flock every ~40 s
            ph = (t + i * 13) % 40
            if ph < 22:
                x = -5 + ph * 10
                y = 30 + 6 * i + 2 * math.sin(ph * 2)
                flap = int(t * 6 + i) % 2
                put(a, x, y, (40, 40, 50))
                put(a, x - 1, y - flap, (40, 40, 50))
                put(a, x + 1, y - flap, (40, 40, 50))


class Birch(Scene):
    """Birch wood under a soft grey sky; yellow leaves drift down, canopy shimmers with the music."""
    seed = 22

    def bg(self):
        grad(self.sky, (150, 170, 190), (210, 218, 212), 0, 90)

    def fg(self):
        L = self.L
        L.ground(lambda x: 88 + math.sin(x / 9), grass=(110, 150, 70))
        self.canopy = []
        for x in range(6, W, 20):
            x += L.r.randrange(-3, 4)
            top = L.r.randrange(16, 30)
            for y in range(top, 90):
                for k in range(3):
                    L.put(x + k, y, (215, 215, 205) if L.r.random() > 0.18 else (40, 40, 40), 4)
            for y in range(top - 16, top + 6):
                for xx in range(x - 8, x + 11):
                    if L.r.random() < 0.75 and abs(xx - x - 1) + abs(y - top + 4) < 12:
                        L.put(xx, y, L.r.choice([(128, 167, 85), (110, 150, 70), (150, 185, 100)]))
                        self.canopy.append((xx, y))

    def behind(self, a, t, lv):
        draw_clouds(a, t, 5, 5, 30, speed=0.3, col=(225, 228, 232), alpha=0.8)

    def front(self, a, t, lv):
        r = random.Random(int(t * 3))                              # shimmer: a few canopy pixels light up
        for _ in range(int(4 + 30 * lv)):
            x, y = self.canopy[r.randrange(len(self.canopy))]
            put(a, x, y, (200, 225, 140), 0.8)
        ps, period = particles(7, 26, 14.0)
        for i, (p0, p1, p2, p3) in enumerate(ps):
            age = (t + p0 * period) % period
            x = p1 * W + 6 * math.sin(age * 1.3 + p2 * 6) + age * 1.5
            y = 10 + age * (5 + 3 * p3)
            if y < 90:
                put(a, x % W, y, (235, 195, 70) if i % 3 else (220, 150, 50))


class Pebble(Scene):
    """Bright meadow with a winding pebble path; flowers bob to the beat, butterflies wander."""
    seed = 33

    def bg(self):
        grad(self.sky, (100, 160, 255), (175, 215, 255), 0, 70)

    def fg(self):
        L = self.L
        L.ground(lambda x: 64 + 2 * math.sin(x / 15), grass=(110, 185, 60), dirt=(96, 160, 52), depth=60)
        for i in range(20):
            t = i / 19
            x, y = 96 + 30 * math.sin(t * 3.2) * t, 66 + 40 * t
            L.disc(x, y, 1.2 + 3.6 * t, L.r.choice([(140, 140, 140), (160, 155, 150), (120, 120, 125)]), 8)
        L.tree(22, 65, size=1.0)
        L.tree(170, 64, size=1.2)
        self.flowers = [(L.r.randrange(W), L.r.randrange(68, 104),
                         L.r.choice([(230, 60, 50), (250, 220, 60), (240, 240, 240), (120, 150, 250)]))
                        for _ in range(60)]

    def behind(self, a, t, lv):
        draw_clouds(a, t, 9, 8, 40, speed=1.0)

    def front(self, a, t, lv):
        bob = lv > 0.55
        for x, y, col in self.flowers:
            dy = -1 if (bob and (x + y) % 2) else 0
            put(a, x, y + 1 + dy, (60, 120, 40))
            put(a, x, y + dy, col)
        for i, col in enumerate([(250, 170, 60), (240, 240, 255), (170, 120, 240)]):
            x = 96 + 70 * math.sin(t * 0.13 + i * 2.1) + 8 * math.sin(t * 0.9 + i)
            y = 55 + 12 * math.sin(t * 0.21 + i * 1.3) + 3 * math.sin(t * 2.3 + i)
            flap = int(t * 8 + i) % 2
            put(a, x, y, (40, 30, 30))
            put(a, x - 1, y - flap, col)
            put(a, x + 1, y - flap, col)


class Lantern(Scene):
    """Night: twinkling stars, a slow moon, the lantern breathing with the music, fireflies."""
    seed = 44

    def bg(self):
        grad(self.sky, (8, 12, 36), (35, 45, 90), 0, 95)
        self.stars = [(self.r.randrange(W), self.r.randrange(80), self.r.random()) for _ in range(140)]

    def fg(self):
        L = self.L
        L.ground(lambda x: 94 + math.sin(x / 11), grass=(40, 70, 40), dirt=(60, 45, 35))
        for x in range(10, W, 14):                                # a fence line
            L.rect(x, 82, x + 2, 95, (95, 72, 45), 6)
        L.rect(10, 85, W - 10, 86, (95, 72, 45), 6)
        L.rect(10, 89, W - 10, 90, (95, 72, 45), 6)
        L.rect(80, 30, 83, 95, (95, 72, 45), 6)                    # lantern post + arm
        L.rect(80, 30, 102, 32, (95, 72, 45), 6)
        L.rect(98, 32, 99, 37, (50, 50, 50), 0)
        L.rect(95, 37, 102, 47, (60, 60, 70), 4)
        L.tree(160, 95, leaves=((30, 60, 30), (38, 72, 36), (24, 50, 26)), trunk=(60, 45, 30), size=1.4)

    def behind(self, a, t, lv):
        for x, y, ph in self.stars:
            b = 0.5 + 0.5 * math.sin(t * (0.8 + ph * 2) + ph * 20)
            put(a, x, y, (235, 235, 255), 0.25 + 0.75 * b)
        mx = 150 - 40 * t / self.T
        rect(a, mx, 12, mx + 10, 22, (230, 230, 210))
        rect(a, mx, 12, mx + 4, 22, (40, 50, 90))

    def front(self, a, t, lv):
        flick = 0.4 + 0.3 * lv + 0.05 * math.sin(t * 17) * math.sin(t * 5.3)
        glow(a, 98.5, 42, 34, (255, 180, 80), flick)
        rect(a, 96, 39, 101, 45, mix((230, 170, 70), (255, 230, 140), min(1, lv)))
        for i in range(18):
            r = random.Random(i)
            x = r.random() * W + 14 * math.sin(t * (0.2 + 0.2 * r.random()) + i)
            y = 60 + r.random() * 30 + 6 * math.sin(t * (0.3 + 0.3 * r.random()) + i * 2)
            on = math.sin(t * (1 + r.random()) + i * 3) > 0.2
            if on:
                put(a, x % W, y, (220, 255, 120))


class Dripstone(Scene):
    """Cave: drops fall from the stalactite tips into the pool and ring out; glow lichen pulses with the music."""
    seed = 55

    def fg(self):
        L = self.L
        for y in range(H):
            for x in range(W):
                L.put(x, y, (52, 48, 46), 22)
        self.tips = []
        for x0 in range(3, W, 8):
            h = L.r.randrange(8, 40)
            w = L.r.randrange(2, 5)
            for y in range(h):
                half = w * (1 - y / h)
                for x in range(int(x0 - half), int(x0 + half) + 1):
                    L.put(x, y, (132, 102, 82), 12)
            self.tips.append((x0, h))
        for x0 in range(6, W, 13):
            h = L.r.randrange(6, 22)
            for y in range(h):
                half = 3 * (1 - y / h)
                for x in range(int(x0 - half), int(x0 + half) + 1):
                    L.put(x, 92 - y, (122, 95, 78), 12)
        L.rect(0, 92, W, H, (40, 70, 120), 10)
        self.lichen = [(int(30 + L.np.normal(0, 12)), int(70 + L.np.normal(0, 8))) for _ in range(60)] + \
                      [(int(160 + L.np.normal(0, 10)), int(55 + L.np.normal(0, 8))) for _ in range(40)]

    def front(self, a, t, lv):
        for x, y in self.lichen:
            put(a, x, y, (130, 230, 170), 0.35 + 0.6 * lv)
        glow(a, 30, 70, 26, (110, 200, 160), 0.12 + 0.25 * lv, steps=4)
        glow(a, 160, 55, 22, (110, 200, 160), 0.1 + 0.2 * lv, steps=4)
        for i, (x0, h) in enumerate(self.tips):                   # each tip drips on its own slow cycle
            r = random.Random(i)
            period = 5 + 9 * r.random()
            age = (t + r.random() * period) % period
            fall = age - (period - 1.6)
            if fall < 0:
                if age > period - 3.5:                            # drop swelling at the tip
                    put(a, x0, h, (120, 200, 255))
                continue
            y = h + 0.5 * 60 * fall * fall
            if y < 92:
                put(a, x0, y, (140, 210, 255))
                put(a, x0, y - 1, (90, 160, 220), 0.5)
            else:
                ring = (fall - math.sqrt(2 * (92 - h) / 60)) * 10
                if 0 <= ring < 7:
                    for dx in (-int(ring), int(ring)):
                        put(a, x0 + dx, 92, (170, 220, 255), 1 - ring / 7)


class Disc(Scene):
    """A music disc spinning on a jukebox; note particles pop out on the music's onsets (like a jukebox)."""
    seed = 66
    label, label2 = (230, 150, 40), (255, 210, 120)

    def wall(self):
        L = self.L
        for y in range(H):
            for x in range(W):
                plank = (y // 8) % 2
                col = (110, 74, 44) if plank else (98, 66, 39)
                if y % 8 == 0 or (x + 30 * plank) % 33 == 0:
                    col = (70, 46, 28)
                L.put(x, y, col, 7)

    def fg(self):
        self.wall()
        self.cx, self.cy, self.R = 96, 50, 40
        d = np.sqrt((XX - self.cx + 0.5) ** 2 + (YY - self.cy + 0.5) ** 2)
        self.d, self.th = d, np.arctan2(YY - self.cy + 0.5, XX - self.cx + 0.5)
        self.inside = d <= self.R
        rng = np.random.default_rng(3)
        self.scratch = rng.random((H, W)) < 0.04

    def disc(self, a, t, lv):
        ang = t * 2 * math.pi * 33.3 / 60
        th = (self.th - ang) % (2 * math.pi)
        d = self.d
        g = 22 + 12 * ((d.astype(int) % 3) == 0)
        img = np.stack([g, g, g + 3], -1).astype(np.float32)
        img[self.scratch & (th < 1.2) & (d > 13)] += 18           # wear marks that turn with the disc
        lab = d <= 12
        img[lab] = self.label
        arc = (d >= 6.5) & (d <= 8) & (th < 3.6)
        img[arc] = self.label2
        dot = (d >= 9.5) & (d <= 10.8) & (th > 4.4) & (th < 4.9)
        img[dot] = (40, 30, 20)
        img[d <= 1.6] = (15, 15, 15)
        spec = (np.abs(((XX - self.cx) - (YY - self.cy) * 0.9) + 0) < 1.2) & (d > 14) & (d < 34) & (XX < self.cx)
        img[spec] += 70 * (0.6 + 0.4 * lv)
        a[self.inside] = img[self.inside]

    def front(self, a, t, lv):
        glow(a, self.cx, self.cy, 60, self.label, 0.08 + 0.18 * lv, steps=4)
        self.disc(a, t, lv)
        for k, (ot, strength) in enumerate(self.onsets):
            age = t - ot
            if 0 <= age < 3.0:
                r = random.Random(k)
                side = -1 if r.random() < 0.5 else 1
                x = self.cx + side * (self.R + 4 + 10 * r.random()) + 3 * math.sin(age * 3 + k)
                y = self.cy + 10 - age * 14 - 20 * r.random()
                draw_note(a, x, y, hue(r.random()), max(0, 1 - age / 3))


class DiscAmber(Disc):
    seed = 67


class DiscPiston(Disc):
    """Same jukebox idea on stone bricks; redstone wiring lights up with the bass, the piston fires on kicks."""
    seed = 68
    label, label2 = (60, 200, 80), (200, 250, 120)

    def wall(self):
        L = self.L
        for y in range(H):
            for x in range(W):
                brick = ((y // 6) % 2) * 6
                col = (120, 120, 120) if (y % 6 and (x + brick) % 12) else (85, 85, 85)
                L.put(x, y, col, 8)

    def front(self, a, t, lv):
        kick = 0.0
        for ot, s in self.onsets:
            if 0 <= t - ot < 0.25:
                kick = max(kick, s * (1 - (t - ot) / 0.25))
        red = mix((90, 10, 10), (255, 40, 30), min(1, 0.3 + kick + 0.4 * lv))
        for x in range(W):
            put(a, x, 100 - int(4 * abs(math.sin(x / 9))), red)
        for y in range(6, 100):
            put(a, 16, y, red)
        ext = int(10 * kick)                                       # piston: base block + extending head
        rect(a, 8, 20, 24, 36, (110, 110, 110))
        rect(a, 14, 36, 18, 36 + ext, (150, 120, 80))
        rect(a, 8, 36 + ext, 24, 40 + ext, (170, 130, 80))
        super().front(a, t, lv)


class Kelp(Scene):
    """Underwater: shimmering light shafts, swaying kelp, fish crossing, bubbles rising."""
    seed = 88

    def bg(self):
        grad(self.sky, (70, 160, 200), (8, 30, 70), 0, H, band=4)

    def fg(self):
        self.L.ground(lambda x: 98 + 2 * math.sin(x / 7), grass=(200, 190, 130), dirt=(180, 170, 115),
                      stone=(150, 140, 100))
        self.kelp = [(x + self.r.randrange(-3, 4), self.r.randrange(40, 85)) for x in range(6, W, 11)]

    def behind(self, a, t, lv):
        for k in range(8):
            x0 = (k * 27 + 8 * math.sin(t * 0.2 + k)) % (W + 40) - 20
            for y in range(0, 85):
                x = int(x0 + y * 0.35)
                for d in range(3):
                    if 0 <= x + d < W:
                        a[y, x + d] = a[y, x + d] * 0.86 + np.array([140, 210, 230]) * 0.14 * (1 - y / 90)
        for i in range(4):                                         # fish crossing
            r = random.Random(i)
            period = 25 + 20 * r.random()
            ph = ((t + r.random() * period) % period) / period
            dirn = 1 if i % 2 else -1
            x = -10 + ph * (W + 20) if dirn > 0 else W + 10 - ph * (W + 20)
            y = 20 + 50 * r.random() + 3 * math.sin(t + i)
            col = [(240, 140, 50), (250, 230, 80), (230, 100, 140), (120, 200, 230)][i]
            rect(a, x, y, x + 5, y + 3, col)
            put(a, x - dirn * 1, y + 1, col)
            put(a, x + (4 if dirn > 0 else 0), y + 1, (20, 20, 20))

    def front(self, a, t, lv):
        for k, (x0, h) in enumerate(self.kelp):
            for y in range(h):
                sway = (2 + 4 * y / h) * math.sin(t * 0.7 + k * 0.9 - y / 12)
                x = int(x0 + sway)
                yy = 98 - y
                put(a, x, yy, (50, 120, 40))
                put(a, x + 1, yy, (40, 100, 35))
                if y % 7 == 3:
                    put(a, x + 2, yy, (90, 160, 50))
        ps, period = particles(9, 40, 9.0)
        for (p0, p1, p2, p3) in ps:
            age = (t + p0 * period) % period
            x = p1 * W + 1.5 * math.sin(age * 3 + p2 * 6)
            y = 98 - age * (9 + 5 * p3)
            if y > 0:
                put(a, x, y, (200, 240, 255), 0.9)
                if p3 > 0.6:
                    put(a, x + 1, y - 1, (170, 220, 245), 0.7)


class Basalt(Scene):
    """Nether basalt deltas: lava seams flicker with the music, ash drifts, embers rise."""
    seed = 99

    def bg(self):
        grad(self.sky, (55, 40, 58), (140, 90, 90), 0, H, band=4)

    def fg(self):
        L = self.L
        x0 = -2
        while x0 < W:
            h = L.r.randrange(30, 85)
            w = L.r.randrange(6, 10)
            for y in range(H - h, H):
                for x in range(x0, x0 + w):
                    L.put(x, y, (75, 75, 80) if (x - x0) % 3 else (55, 55, 60), 10)
            L.rect(x0, H - h, x0 + w, H - h + 1, (110, 110, 118), 5)
            x0 += w + L.r.randrange(0, 4)
        self.lava = [(L.r.randrange(W), L.r.randrange(88, 104)) for _ in range(6)]

    def behind(self, a, t, lv):
        draw_clouds(a, t, 12, 5, 40, speed=0.4, col=(120, 80, 90), alpha=0.5)

    def front(self, a, t, lv):
        for i, (x, y) in enumerate(self.lava):
            f = 0.35 + 0.35 * lv + 0.08 * math.sin(t * 5 + i * 2)
            glow(a, x, y, 14, (255, 110, 20), f, steps=4)
            rect(a, x - 5, y, x + 5, y + 2, (255, 150 + 60 * lv, 30))
        ps, period = particles(13, 90, 20.0)
        for (p0, p1, p2, p3) in ps:
            age = (t + p0 * period) % period
            put(a, (p1 * W + age * 2 + 3 * math.sin(age + p2 * 6)) % W, (p3 * H + age * 3) % H,
                (200, 200, 200) if p2 > 0.5 else (140, 140, 140))
        ps, period = particles(14, 14, 6.0)
        for (p0, p1, p2, p3) in ps:
            age = (t + p0 * period) % period
            x = self.lava[int(p1 * len(self.lava))][0] + 4 * math.sin(age * 2 + p2 * 6)
            y = 95 - age * (10 + 6 * p3)
            put(a, x, y, (255, 170, 60), max(0, 1 - age / period))


class Hearth(Scene):
    """Village evening that slowly becomes night: chimney smoke, flickering window, first stars."""
    seed = 101

    def fg(self):
        L = self.L
        L.ground(lambda x: 86 + math.sin(x / 10))
        x0, x1 = 70, 116
        L.rect(x0, 60, x1, 87, (162, 130, 78), 8)
        for y in range(60, 87, 4):
            L.rect(x0, y, x1, y + 1, (130, 100, 60), 3)
        L.rect(x0, 84, x1, 87, (120, 120, 120), 14)
        for k in range(16):
            L.rect(x0 - 4 + k, 60 - k, x1 + 4 - k, 61 - k, (90, 60, 40), 8)
        L.rect(80, 66, 90, 76, (255, 210, 110), 0)
        L.rect(84, 66, 85, 76, (90, 60, 40), 0)
        L.rect(98, 69, 105, 87, (100, 70, 40), 6)
        L.rect(104, 38, 109, 56, (120, 120, 120), 12)
        L.tree(140, 87, size=1.2)
        L.tree(30, 87, size=1.0)
        L.rect(158, 80, 166, 87, (120, 120, 120), 14)              # campfire stones / well
        self.win = (85, 71)

    def sky_at(self, t):
        p = min(1.0, t / self.T)
        a = np.zeros((H, W, 3), dtype=np.float32)
        grad(a, mix((80, 70, 140), (12, 14, 40), p), mix((250, 150, 100), (60, 50, 90), p), 0, 90)
        r = random.Random(5)
        for _ in range(90):
            x, y, ph = r.randrange(W), r.randrange(70), r.random()
            put(a, x, y, (235, 235, 255), max(0, (p - 0.45 - ph * 0.3) * 3))
        return a

    def behind(self, a, t, lv):
        p = min(1.0, t / self.T)
        draw_clouds(a, t, 21, 4, 30, speed=0.5, col=mix((255, 190, 170), (60, 60, 90), p), alpha=0.9)
        for i in range(10):                                        # smoke
            age = (t + i * 1.4) % 14
            x = 106.5 + age * 2.2 + 2 * math.sin(age + i)
            y = 36 - age * 3
            s = 2 + age * 0.25
            rect(a, x - s / 2, y - s / 2, x + s / 2, y + s / 2, (200, 195, 200), max(0, 0.8 - age / 14))

    def front(self, a, t, lv):
        p = min(1.0, t / self.T)
        f = 0.25 + 0.3 * p + 0.15 * lv + 0.05 * math.sin(t * 9) * math.sin(t * 3.1)
        glow(a, 85, 71, 22, (255, 200, 90), f, steps=4)
        a[:, :] *= 1 - 0.35 * p                                    # night falls on the land too
        glow(a, 85, 71, 9, (255, 210, 110), 0.5)
        rect(a, 80, 66, 90, 76, (255, 215, 120))
        rect(a, 84, 66, 85, 76, (70, 45, 30))
        glow(a, 162, 78, 12, (255, 140, 40), 0.3 + 0.3 * lv, steps=4)
        for i in range(5):
            put(a, 159 + i * 1.5, 79 - (int(t * 9 + i * 3) % 3), (255, 160 + 20 * i, 40))


class Void(Scene):
    """The End: stars, crystals pulsing with the music, a dragon passing, drifting purple particles."""
    seed = 111

    def bg(self):
        grad(self.sky, (8, 0, 15), (30, 10, 40), 0, H)
        self.stars = [(self.r.randrange(W), self.r.randrange(H), self.r.random()) for _ in range(180)]

    def fg(self):
        L = self.L
        for x in range(20, 172):
            top = 80 + int(2 * math.sin(x / 6))
            depth = int(20 * math.sqrt(max(0, 1 - ((x - 96) / 76) ** 2))) + L.r.randrange(0, 3)
            for y in range(top, min(H, top + depth)):
                L.put(x, y, (219, 222, 158), 8)
        self.pillars = [(40, 50), (70, 64), (96, 40), (124, 70), (152, 52)]
        for x0, h in self.pillars:
            L.rect(x0, 80 - h, x0 + 7, 81, (25, 15, 40), 25)
        L.rect(88, 72, 104, 76, (30, 60, 50), 5)
        L.rect(90, 73, 102, 75, (10, 10, 25), 5)

    def behind(self, a, t, lv):
        for x, y, ph in self.stars:
            put(a, x, y, (230, 200, 255), 0.3 + 0.6 * (0.5 + 0.5 * math.sin(t * (0.5 + ph) + ph * 30)))
        ph = (t % 70) / 70                                         # dragon crossing behind the pillars
        if ph < 0.6:
            x = -20 + ph / 0.6 * (W + 40)
            y = 30 + 8 * math.sin(ph * 9)
            flap = math.sin(t * 5)
            rect(a, x, y, x + 12, y + 3, (20, 10, 25))
            rect(a, x + 12, y - 1, x + 16, y + 2, (20, 10, 25))
            put(a, x + 14, y, (220, 80, 255))
            for k in range(8):
                wy = y - int(flap * (k / 2))
                put(a, x + 3 + k, wy - 1, (25, 15, 30))
                put(a, x + 3 + k, wy - 2, (25, 15, 30))
            rect(a, x - 8, y + 1, x, y + 2, (20, 10, 25))

    def front(self, a, t, lv):
        for i, (x0, h) in enumerate(self.pillars):
            s = 0.3 + 0.6 * lv + 0.1 * math.sin(t * 2 + i)
            glow(a, x0 + 3.5, 76 - h, 10, (255, 120, 220), s, steps=4)
            rect(a, x0 + 1, 72 - h, x0 + 6, 78 - h, mix((230, 120, 210), (255, 220, 250), min(1, lv)))
        ps, period = particles(17, 40, 10.0)
        for (p0, p1, p2, p3) in ps:
            age = (t + p0 * period) % period
            put(a, p1 * W + 3 * math.sin(age + p2 * 6), p3 * H - age * 2, (170, 60, 220), max(0, 1 - age / period))


class Home(Scene):
    """Credits: the sun sets into the sea over the whole track while a small figure walks the path home."""
    seed = 121

    def fg(self):
        L = self.L
        L.ground(lambda x: 76 + 0.0035 * x * x if x < 120 else H, grass=(70, 120, 45))
        self.path = []
        for k in range(60):
            t = k / 59
            x = 4 + 80 * t
            y = 76 + 0.0035 * x * x
            self.path.append((x, y))
        for x, y in self.path:
            L.rect(x, y + 1, x + 3, y + 3, (150, 120, 80), 6)
        hx = 8                                                     # the house the walker heads to
        hy = 77
        L.rect(hx, hy - 10, hx + 12, hy, (162, 130, 78), 8)
        for k in range(7):
            L.rect(hx - 2 + k, hy - 10 - k, hx + 14 - k, hy - 9 - k, (90, 60, 40), 8)
        L.rect(hx + 4, hy - 7, hx + 8, hy - 3, (255, 210, 110), 0)

    def sky_at(self, t):
        p = min(1.0, t / self.T)
        a = np.zeros((H, W, 3), dtype=np.float32)
        grad(a, mix((60, 40, 100), (10, 10, 35), p), mix((250, 140, 70), (90, 50, 80), p), 0, 66)
        sy = 40 + 30 * p
        glow(a, 120, sy + 7, 40, (255, 170, 90), 0.4 * (1 - p))
        rect(a, 108, sy, 132, sy + 14, (255, 200, 110))
        r = random.Random(8)
        for _ in range(100):
            x, y, ph = r.randrange(W), r.randrange(60), r.random()
            put(a, x, y, (235, 235, 255), max(0, (p - 0.6 - ph * 0.2) * 3))
        a[66:, :] = 0
        for y in range(66, H):
            a[y, :] = mix((40, 60, 110), (10, 15, 40), p)
        return a

    def behind(self, a, t, lv):
        p = min(1.0, t / self.T)
        for y in range(66, H):                                     # sun path on the water
            for x in range(108, 132):
                if (x + y + int(t * 4)) % 5 == 0 and random.Random(x * 131 + y).random() < 0.7:
                    put(a, x + 2 * math.sin(t + y), y, (250, 180, 100), max(0, 0.9 - p))
        for i in range(30):
            r = random.Random(i)
            x = (r.random() * W + t * (1 + r.random())) % W
            y = 68 + r.random() * 38
            put(a, x, y, (90, 120, 170), 0.6)

    def front(self, a, t, lv):
        p = min(1.0, t / self.T)
        a[:, :] *= 1 - 0.3 * p
        glow(a, 14, 72, 10, (255, 210, 110), 0.3 + 0.3 * p, steps=4)
        rect(a, 12, 70, 16, 74, (255, 215, 120))
        k = min(len(self.path) - 1, int((1 - p) * (len(self.path) - 1)))  # walks from right to left, home
        x, y = self.path[k]
        step = int(t * 3) % 2
        rect(a, x, y - 8, x + 2, y - 3, (60, 110, 170))
        rect(a, x, y - 10, x + 2, y - 8, (200, 150, 110))
        put(a, x + step, y - 2, (40, 40, 80))
        put(a, x + 1 - step, y - 1, (40, 40, 80))
        put(a, x + step, y - 1, (40, 40, 80))


class Lichen(Scene):
    """Cobblestone wall slowly overgrown by lichen over the track; spores drift."""
    seed = 131

    def fg(self):
        L = self.L
        for y in range(H):
            for x in range(W):
                cell = ((x // 7 + (y // 6) * 3) * 37) % 5
                col = [(120, 120, 120), (105, 105, 105), (135, 135, 135), (95, 95, 98), (115, 112, 108)][cell]
                if x % 7 == 0 or y % 6 == 0:
                    col = (70, 70, 72)
                L.put(x, y, col, 10)
        pts = []
        for _ in range(26):
            cx, cy = L.r.randrange(W), L.r.randrange(H)
            for _ in range(90):
                pts.append((int(cx + L.np.normal(0, 5)), int(cy + L.np.normal(0, 3.5)),
                            L.r.choice([(110, 140, 70), (160, 175, 110), (90, 120, 60), (190, 190, 140)])))
        L.r.shuffle(pts)
        self.growth = pts

    def front(self, a, t, lv):
        p = min(1.0, 0.15 + 0.85 * t / self.T)
        for x, y, col in self.growth[:int(len(self.growth) * p)]:
            put(a, x, y, col)
        ps, period = particles(19, 30, 12.0)
        for (p0, p1, p2, p3) in ps:
            age = (t + p0 * period) % period
            put(a, (p1 * W + age * 3) % W, p2 * H - age * 1.5 + 2 * math.sin(age * 2 + p3 * 6), (220, 230, 170),
                0.6 * math.sin(math.pi * age / period))


SCENES = {1: Spawn, 2: Birch, 3: Pebble, 4: Lantern, 5: Dripstone, 6: DiscAmber, 7: DiscPiston, 8: Kelp,
          9: Basalt, 10: Hearth, 11: Void, 12: Home, 13: Lichen}


# ---------------------------------------------------------------- audio analysis
def analyse(wav):
    from scipy.signal import butter, sosfilt
    a, sr = sf.read(wav, dtype="float32")
    m = a.mean(1)
    hop = sr // FPS
    nfr = len(m) // hop + 1
    pad = np.zeros(nfr * hop, dtype=np.float32)
    pad[:len(m)] = m
    rms = np.sqrt((pad.reshape(nfr, hop) ** 2).mean(1))
    db = 20 * np.log10(rms + 1e-6)
    lo, hi = np.percentile(db, 10), np.percentile(db, 97)
    env = np.clip((db - lo) / (hi - lo + 1e-6), 0, 1)
    env = np.convolve(env, np.ones(5) / 5, mode="same")           # ~0.2 s smoothing
    low = sosfilt(butter(4, 160, "lp", fs=sr, output="sos"), pad)
    lrms = np.sqrt((low.reshape(nfr, hop) ** 2).mean(1))
    full = np.sqrt((pad.reshape(nfr, hop) ** 2).mean(1))
    onsets = []
    for sig, thr in ((lrms, 1.4), (full, 1.5)):                   # rising edges well above the local average
        loc = np.convolve(sig, np.ones(24) / 24, mode="same") + 1e-6
        ratio = sig / loc
        last = -99
        for i in range(1, nfr):
            if ratio[i] > thr and ratio[i - 1] <= thr and i - last > 5 and sig[i] > np.percentile(sig, 40):
                onsets.append((i / FPS, float(min(1, (ratio[i] - 1) / 1.5))))
                last = i
    onsets.sort()
    return len(m) / sr, env, onsets


# ---------------------------------------------------------------- titles & render
def blend_text(a, s, x, y, col, alpha, scale=1, shadow=(20, 20, 20)):
    if alpha <= 0:
        return
    tmp = a.copy()
    text(tmp, s, x, y, col, shadow=shadow, scale=scale)
    a[:] = a * (1 - alpha) + tmp * alpha


def overlay(a, num, title, t, T):
    up = min(1, max(0, t - 0.8) / 1.2) * min(1, max(0, 8.5 - t) / 1.5)  # big title card, 1-8.5 s
    if up > 0:
        band = a[38:72].copy() * 0.4
        a[38:72] = a[38:72] * (1 - up) + band * up
        s = title.upper()
        blend_text(a, s, (W - text_w(s) * 2) // 2, 42, (255, 255, 255), up, scale=2)
        sub = f"{ALBUM_NAME.upper()}  {num:02d}"
        blend_text(a, sub, (W - text_w(sub)) // 2, 61, (255, 255, 160), up)
    small = min(1, max(0, t - 8.5) / 2) * min(1, max(0, T - t) / 2)
    if small > 0:
        s = f"{num:02d} {title.upper()}"
        blend_text(a, s, 3, H - 9, (255, 255, 255), 0.75 * small)


def encode(frames_fn, n, wav, out, extra_audio_args=()):
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-"]
    cmd += ["-i", str(wav)] if wav else ["-f", "lavfi", "-t", str(n / FPS), "-i", "anullsrc=r=48000:cl=stereo"]
    cmd += ["-vf", f"scale={W * SCALE}:{H * SCALE}:flags=neighbor,format=yuv420p", "-c:v", "libx264",
            "-preset", "medium", "-tune", "animation", "-crf", "18", "-r", str(FPS), "-g", str(FPS * 4),
            "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-shortest", "-movflags", "+faststart", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(np.clip(frames_fn(i), 0, 255).astype(np.uint8).tobytes())
    p.stdin.close()
    if p.wait():
        raise RuntimeError(f"ffmpeg failed for {out}")


def make_scene(k):
    slug, _ = TRACKS[k]
    wav = OUT / f"{k:02d}_{slug}.wav"
    T, env, onsets = analyse(wav)
    return SCENES[k](T, env, onsets), T, env, wav


def render_track(k):
    slug, title = TRACKS[k]
    sc, T, env, wav = make_scene(k)
    n = int(math.ceil(T * FPS))

    def fr(i):
        t = i / FPS
        a = sc.frame(t, float(env[min(i, len(env) - 1)]))
        overlay(a, k, title, t, T)
        a *= max(0.0, min(1.0, t / 1.0, (T - t) / 1.5))            # fade in / out
        return a

    out = VID / f"{k:02d}_{slug}.mp4"
    encode(fr, n, wav, out)
    return str(out), T


def stills(k, times=(0.2, 0.5, 0.85)):
    from PIL import Image
    slug, title = TRACKS[k]
    sc, T, env, _ = make_scene(k)
    (VID / "stills").mkdir(exist_ok=True)
    for f in times:
        t = T * f
        a = sc.frame(t, float(env[min(int(t * FPS), len(env) - 1)]))
        overlay(a, k, title, t if f > 0.1 else 4.0, T)
        Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((W * 5, H * 5), Image.NEAREST).save(
            VID / "stills" / f"{k:02d}_{slug}_{int(f * 100):02d}.png")


def album_video(results):
    """Concatenate track videos with short cover-card gaps; write YouTube description with chapters."""
    from PIL import Image
    cov = np.asarray(Image.open(ALBUM / "art/cover.png").convert("RGB").resize((100, 100), Image.NEAREST),
                     dtype=np.float32)
    card = np.zeros((H, W, 3), dtype=np.float32)
    grad(card, (120, 170, 240), (200, 225, 250), 0, H, band=4)
    card[4:104, 46:146] = cov
    gap = VID / "gap.mp4"
    encode(lambda i: card * min(1, i / 12, (GAP * FPS - i) / 12), int(GAP * FPS), None, gap)
    lst = VID / "concat.txt"
    lines, chapters, t = [], [], 0.0
    for k in sorted(results):
        path, T = results[k]
        if lines:
            lines.append(f"file '{gap}'")
            t += GAP
        chapters.append(f"{int(t // 60):02d}:{int(t % 60):02d} {TRACKS[k][1]}")
        lines.append(f"file '{path}'")
        t += T
    lst.write_text("\n".join(lines) + "\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                    "-movflags", "+faststart", str(VID / "Volume_Gamma_full_album.mp4")], check=True)
    desc = [f"{ALBUM_NAME} — an album of original music in the spirit of C418's Minecraft soundtrack.",
            "Composed, produced and animated by Claude (Anthropic). Not affiliated with Mojang, Microsoft or C418.", "",
            "Tracklist:"] + chapters
    (VID / "youtube_description.txt").write_text("\n".join(desc) + "\n")
    print("\n".join(chapters))


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--still":
        for k in map(int, args[1:] or TRACKS):
            stills(k)
        sys.exit()
    ks = list(map(int, args)) if args else sorted(TRACKS)
    with ProcessPoolExecutor(max_workers=6) as ex:
        results = dict(zip(ks, ex.map(render_track, ks)))
    for k, (p, T) in results.items():
        print(f"{p}  {T:.1f}s")
    if not args:
        album_video(results)
