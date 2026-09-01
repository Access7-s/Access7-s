"""Topographic contour lines, generated as real isolines.

A smooth scalar field is built from a handful of sinusoids (deterministic,
seeded, and periodic in x so the field has no seam), then marching squares
extracts the isolines at evenly spaced levels. The resulting segments are
chained into polylines so the SVG stays small.
"""

import math
import random

# Marching-squares case table.
# Corner bits, clockwise from top-left: b0=(i,j) b1=(i+1,j) b2=(i+1,j+1) b3=(i,j+1)
# Edges: 0=top, 1=right, 2=bottom, 3=left
CASES = {
    0: [], 1: [(3, 0)], 2: [(0, 1)], 3: [(3, 1)],
    4: [(1, 2)], 5: [(3, 0), (1, 2)], 6: [(0, 2)], 7: [(3, 2)],
    8: [(2, 3)], 9: [(2, 0)], 10: [(0, 1), (2, 3)], 11: [(2, 1)],
    12: [(1, 3)], 13: [(1, 0)], 14: [(0, 3)], 15: [],
}


def make_field(w, h, step, seed=7, octaves=5):
    """Sample a smooth height field on a grid, periodic in x."""
    rng = random.Random(seed)
    aspect = w / h
    waves = []
    for k in range(octaves):
        # Each wave gets its own direction, otherwise every octave lines up and
        # the field turns into parallel diagonal banding instead of topography.
        # f is in cycles per height; the direction is decomposed into x and y
        # components, and fx is rounded to an integer so the field stays
        # periodic across the width (no visible seam).
        f = rng.uniform(0.8, 1.5) * (1.7 ** k)
        theta = rng.uniform(0, math.tau)
        fx = round(f * aspect * math.cos(theta))
        fy = f * math.sin(theta)
        ph = rng.uniform(0, math.tau)
        amp = 1.0 / (1.7 ** k)
        waves.append((fx, fy, ph, amp))

    nx = w // step + 1
    ny = h // step + 1
    grid = []
    for j in range(ny):
        v = j * step / h
        row = []
        for i in range(nx):
            u = i * step / w
            t = 0.0
            for fx, fy, ph, amp in waves:
                t += amp * math.sin(math.tau * (fx * u + fy * v) + ph)
            row.append(t)
        grid.append(row)
    return grid, nx, ny


def _point(edge, i, j, v, level, step):
    """Interpolated crossing point on one cell edge, in pixels."""
    v00, v10, v11, v01 = v

    def lerp(a, b):
        d = b - a
        return 0.5 if abs(d) < 1e-12 else (level - a) / d

    if edge == 0:
        return ((i + lerp(v00, v10)) * step, j * step)
    if edge == 1:
        return ((i + 1) * step, (j + lerp(v10, v11)) * step)
    if edge == 2:
        return ((i + lerp(v01, v11)) * step, (j + 1) * step)
    return (i * step, (j + lerp(v00, v01)) * step)


def isolines(grid, nx, ny, level, step):
    """Marching squares -> list of segments at one level."""
    segs = []
    for j in range(ny - 1):
        r0, r1 = grid[j], grid[j + 1]
        for i in range(nx - 1):
            v00, v10 = r0[i], r0[i + 1]
            v01, v11 = r1[i], r1[i + 1]
            idx = ((v00 >= level) << 0 | (v10 >= level) << 1 |
                   (v11 >= level) << 2 | (v01 >= level) << 3)
            pairs = CASES[idx]
            if not pairs:
                continue
            v = (v00, v10, v11, v01)
            for a, b in pairs:
                segs.append((_point(a, i, j, v, level, step),
                             _point(b, i, j, v, level, step)))
    return segs


def chain(segs, tol=2):
    """Join segments end-to-end into polylines (keeps the SVG small)."""
    def key(p):
        return (round(p[0] / tol), round(p[1] / tol))

    ends = {}
    for n, (a, b) in enumerate(segs):
        ends.setdefault(key(a), []).append((n, 0))
        ends.setdefault(key(b), []).append((n, 1))

    used = [False] * len(segs)
    paths = []
    for start in range(len(segs)):
        if used[start]:
            continue
        used[start] = True
        a, b = segs[start]
        poly = [a, b]
        # extend forward from b, then backward from a
        for direction in (0, 1):
            if direction:
                poly.reverse()
            while True:
                tip = poly[-1]
                nxt = None
                for n, side in ends.get(key(tip), ()):
                    if not used[n]:
                        nxt = (n, side)
                        break
                if nxt is None:
                    break
                n, side = nxt
                used[n] = True
                poly.append(segs[n][1 - side])
        paths.append(poly)
    return paths


def simplify(poly, min_d=2.2):
    """Drop points that barely move the line."""
    out = [poly[0]]
    for p in poly[1:-1]:
        q = out[-1]
        if (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 >= min_d * min_d:
            out.append(p)
    out.append(poly[-1])
    return out


def contour_paths(w, h, colour, step=6, levels=9, seed=7, width=1.0, octaves=5):
    grid, nx, ny = make_field(w, h, step, seed, octaves)
    flat = [v for row in grid for v in row]
    lo, hi = min(flat), max(flat)
    span = hi - lo

    d = []
    for k in range(1, levels + 1):
        level = lo + span * k / (levels + 1)
        segs = isolines(grid, nx, ny, level, step)
        for poly in chain(segs):
            if len(poly) < 3:
                continue
            poly = simplify(poly)
            if len(poly) < 3:
                continue
            # After the initial moveto, further coordinate pairs are implicit
            # linetos, so "M x y x y x y" is both valid and compact.
            pts = " ".join(f"{x:.0f} {y:.0f}" for x, y in poly)
            d.append("M" + pts)
    body = "".join(f'<path d="{p}"/>' for p in d)
    return (f'<g fill="none" stroke="{colour}" stroke-width="{width}" '
            f'stroke-linejoin="round" stroke-linecap="round">{body}</g>')
