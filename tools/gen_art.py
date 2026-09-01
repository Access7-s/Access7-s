"""Generate Dhaka-inspired SVG art for the profile README.

Dhaka is the Nepali handwoven cross-stitch textile (as on the dhaka topi).
The motifs sit on a square grid, so they map naturally onto SVG rects.

Each motif is emitted once into <defs> and repeated with <use>, and the
background texture is an SVG <pattern>, which keeps the files a few KB
rather than a few hundred.
"""

import os

from contours import contour_paths

W = 1200

THEMES = {
    "light": dict(bg="#FFFFFF", ink="#171717", accent="#C8102E",
                  texture="#E9E9E9", sub="#6A6A6A", rule="#DCDCDC"),
    "dark":  dict(bg="#0D1117", ink="#E6EDF3", accent="#E5484D",
                  texture="#1B2029", sub="#8B949E", rule="#272E38"),
}


def star_cells(r=7, sq=4):
    """Classic 8-pointed Dhaka star.

    The union of a diamond (points on the axes) and a square (points on the
    diagonals) is the standard cross-stitch eight-point star.
    """
    return [(dx, dy)
            for dy in range(-r, r + 1)
            for dx in range(-r, r + 1)
            if abs(dx) + abs(dy) <= r or max(abs(dx), abs(dy)) <= sq]


def diamond_cells(r):
    return [(dx, dy)
            for dy in range(-r, r + 1)
            for dx in range(-r, r + 1)
            if abs(dx) + abs(dy) <= r]


def ring_cells(r):
    """Hollow diamond outline."""
    return [(dx, dy)
            for dy in range(-r, r + 1)
            for dx in range(-r, r + 1)
            if abs(dx) + abs(dy) == r]


def group(gid, cells, cell):
    """Motif as a <g> with no fill, so <use fill=...> colours it by inheritance."""
    body = "".join(
        f'<rect x="{dx*cell}" y="{dy*cell}" width="{cell}" height="{cell}"/>'
        for dx, dy in cells
    )
    return f'<g id="{gid}">{body}</g>'


def use(gid, x, y, colour):
    return f'<use href="#{gid}" x="{x:.0f}" y="{y:.0f}" fill="{colour}"/>'


def band(y, t, cell, unit):
    """Repeating strip: star, then a ring with a dot at its centre."""
    out, x = [], unit // 2
    while x < W + unit:
        out.append(use("star", x, y, t["accent"]))
        out.append(use("ring", x + unit // 2, y, t["ink"]))
        out.append(use("dot", x + unit // 2, y, t["accent"]))
        x += unit
    return "".join(out)


def header(theme):
    t = THEMES[theme]
    h = 220

    # The text block runs from the name's cap-top to the last line's
    # descender. Centring that box (rather than the baselines) is what makes
    # the space above and below come out equal.
    cap, block = 35, 92
    name_y = (h - block) / 2 + cap
    sub1_y = name_y + 32
    sub2_y = name_y + 54

    return "".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" '
        f'viewBox="0 0 {W} {h}" role="img" aria-label="Shubham Neupane">',
        f'<rect width="{W}" height="{h}" fill="{t["bg"]}"/>',
        # Topographic contours: real isolines through a seeded smooth field.
        contour_paths(W, h, t["texture"], step=5, levels=9, seed=11),
        f'<text x="{W//2}" y="{name_y:.0f}" text-anchor="middle" '
        f'font-family="Georgia, \'Times New Roman\', serif" font-size="50" '
        f'letter-spacing="7" fill="{t["ink"]}">SHUBHAM NEUPANE</text>',
        f'<text x="{W//2}" y="{sub1_y:.0f}" text-anchor="middle" '
        f'font-family="Helvetica, Arial, sans-serif" font-size="14" '
        f'letter-spacing="4.5" fill="{t["sub"]}">'
        'TECHNICAL PRODUCT MANAGER &#183; PRODUCT OWNER</text>',
        f'<text x="{W//2}" y="{sub2_y:.0f}" text-anchor="middle" '
        f'font-family="Helvetica, Arial, sans-serif" font-size="12" '
        f'letter-spacing="3" fill="{t["sub"]}">'
        'CO-FOUNDER, AURORA STUDIOS &#183; KATHMANDU, NEPAL</text>',
        '</svg>',
    ])


def divider(theme):
    t = THEMES[theme]
    h, cell, unit = 26, 3, 66
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" '
        f'viewBox="0 0 {W} {h}" role="img" aria-label="">',
        '<defs>',
        group("ring", ring_cells(3), cell),
        group("dot", diamond_cells(1), cell),
        '</defs>',
        f'<rect width="{W}" height="{h}" fill="{t["bg"]}"/>',
    ]
    x = unit // 2
    while x < W + unit:
        out.append(use("ring", x, h // 2, t["accent"]))
        out.append(use("dot", x + unit // 2, h // 2, t["ink"]))
        x += unit
    out.append('</svg>')
    return "".join(out)


if __name__ == "__main__":
    os.makedirs("assets", exist_ok=True)
    for name, fn in (("header", header), ("divider", divider)):
        for theme in ("light", "dark"):
            path = f"assets/{name}-{theme}.svg"
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(fn(theme))
            print(f"wrote {path} ({os.path.getsize(path):,} bytes)")
