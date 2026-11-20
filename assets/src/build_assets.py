"""Build the profile README visuals: assets/*.svg, text converted to outlines.

GitHub serves README images through <img>, where web fonts do not load, so every
string is outlined. Each visual has four files: wide and narrow layouts, light and
dark. The README picks one with <picture> media queries.

Run from the repository root:

    uv run --with fonttools==4.68.0 --with uharfbuzz==0.57.0 --with brotli \
        assets/src/build_assets.py --brand-src <brand>/src --fonts <site>/public/fonts

--brand-src is the OxFoundry brand build folder (text.py and fonts/InterDisplay-*.otf);
--fonts holds the Inter and JetBrains Mono variable woff2 files.
"""
import argparse
import glob
import os
import sys

import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

# Inks are the OxFoundry tokens; the grounds are GitHub's own canvases (#ffffff, #0d1117).
THEMES = {
    "light": {"strong": "#111418", "body": "#2B3139", "mute": "#59626E", "line": "#D7DBE0", "accent": "#2E4C82"},
    "dark": {"strong": "#E9ECEF", "body": "#B8BBBE", "mute": "#9B9FA3", "line": "#32363B", "accent": "#799EE3"},
}

PRODUCTS = [
    {
        "slug": "oxsay",
        "name": "OxSay",
        "line": "Local voice studio for the Mac",
        "proof": "41 releases in 52 days",
        "state": "Apache-2.0",
        "dates": ("2026-09-29", "11-19"),
        "alt": "OxSay: local voice studio for the Mac. 41 releases in 52 days, 2026-09-29 to 2026-11-19. Apache-2.0.",
    },
    {
        "slug": "vaelor",
        "name": "Vaelor",
        "line": "Code intelligence for coding agents",
        "proof": "35+ MCP tools, 16 languages",
        "state": "Apache-2.0",
        "dates": ("2026-02-27", "11-19"),
        "alt": "Vaelor: code intelligence for coding agents. 35+ MCP tools, 16 languages. Apache-2.0.",
    },
    {
        "slug": "oxpulse",
        "name": "OxPulse",
        "line": "Encrypted calls built for about 1 KB/s",
        "proof": "1:1 calls live, group calls in rework",
        "state": "Private source",
        "dates": ("2026-04-03", "now"),
        "alt": "OxPulse: encrypted calls built for about 1 KB/s. 1:1 calls live, group calls in rework. Private source.",
    },
]

# (name, wide-plate lines, narrow-plate line, gate before the step)
STEPS = [
    ("Spec", ["Claude Code and I,", "to my architecture"], "Claude Code and I, to the architecture I set", False),
    ("Implement", ["Devin, isolated", "git worktree"], "Devin, in an isolated git worktree", False),
    ("Review", ["Codex reviews it,", "then I read it"], "Codex reviews the PR, then I read the change", False),
    ("Merge", ["Checks green, head", "is the reviewed one"], "Every check green, head is the reviewed commit", True),
    ("Deploy", ["A GitHub release", "triggers it"], "A GitHub release triggers the deploy", True),
]
KEY = "Gate: the change waits here until the step before it passes."
METHOD_ALT = (
    "One change, from task to deploy: Spec (Claude Code and I), Implement (Devin, in an isolated git "
    "worktree), Review (Codex, then I read the change), a gate, Merge (every check green, the head is the "
    "reviewed commit), a gate, Deploy (a GitHub release triggers it)."
)


def load_fonts(brand_src, fonts_dir):
    sys.path.insert(0, brand_src)
    import text  # the brand's HarfBuzz outliner

    def instance(pattern, wght, name):
        path = glob.glob(os.path.join(fonts_dir, pattern))[0]
        tt = instantiateVariableFont(TTFont(path), {"wght": wght})
        tt.flavor = None
        tmp = os.path.join(os.environ.get("TMPDIR", "/tmp"), name + ".ttf")
        tt.save(tmp)
        face = hb.Face(hb.Blob.from_file_path(tmp))
        tt = TTFont(tmp)
        text._cache[name] = (hb.Font(face), tt, tt.getGlyphSet(), face.upem)

    instance("inter-latin-wght-normal.*.woff2", 480, "body")
    instance("jetbrains-mono-latin-wght-normal.*.woff2", 450, "mono")
    return text.line


class Svg:
    def __init__(self, line, w, h, theme, title):
        self.line, self.w, self.h, self.c, self.title = line, w, h, THEMES[theme], title
        self.parts = []

    def text(self, s, font, size, x, y, ink, anchor="start", tracking=0.0):
        d, width = self.line(s, font, size, 0, 0, tracking)
        if anchor == "end":
            x -= width
        self.parts.append(f'<path transform="translate({x:.2f} {y})" fill="{self.c[ink]}" d="{d}"/>')
        return x + width

    def rule(self, y):
        self.parts.append(f'<path d="M0 {y}H{self.w}" stroke="{self.c["line"]}"/>')

    def arrow(self, x, y, length, ink, width=1.2):
        c = self.c[ink]
        self.parts.append(
            f'<path d="M{x} {y}h{length}m-3.5 -3.5l3.5 3.5l-3.5 3.5" fill="none" stroke="{c}" '
            f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'
        )

    def out_arrow(self, x, y, ink):
        c = self.c[ink]
        self.parts.append(
            f'<path d="M{x} {y + 9}l9 -9m-6.5 0h6.5v6.5" fill="none" stroke="{c}" stroke-width="1.4" '
            'stroke-linecap="round" stroke-linejoin="round"/>'
        )

    def node(self, x, y):
        self.parts.append(f'<circle cx="{x}" cy="{y}" r="4.5" fill="{self.c["strong"]}"/>')

    def gate(self, x, y, s=6.5):
        self.parts.append(f'<path d="M{x} {y - s}l{s} {s}l-{s} {s}l-{s} -{s}z" fill="{self.c["accent"]}"/>')

    def save(self, name):
        body = "".join(self.parts)
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" role="img"><title>{self.title}</title>{body}</svg>\n'
        )
        with open(os.path.join(OUT, name), "w") as f:
            f.write(svg)


def dates(s, p, x, y, size):
    a, b = p["dates"]
    gap, length = size * 0.55, size * 1.1
    end = s.text(a, "mono", size, x, y, "mute")
    s.arrow(end + gap, y - size * 0.36, length, "mute")
    return s.text(b, "mono", size, end + 2 * gap + length, y, "mute")


def product(line, p, theme, wide, first, last):
    if wide:
        s = Svg(line, 680, 80, theme, p["alt"])
        s.text(p["name"], "InterDisplay-SemiBold", 24, 0, 36, "strong", tracking=-0.02)
        s.text(p["line"], "body", 15, 0, 60, "body")
        s.text(p["proof"], "mono", 12.5, 384, 34, "strong")
        end = dates(s, p, 384, 59, 12.5)
        s.text("· " + p["state"], "mono", 12.5, end + 8, 59, "mute")
        s.out_arrow(670, 25, "accent")
    else:
        s = Svg(line, 320, 108, theme, p["alt"])
        s.text(p["name"], "InterDisplay-SemiBold", 21, 0, 34, "strong", tracking=-0.02)
        s.text(p["state"], "mono", 10.5, 304, 33, "mute", anchor="end")
        s.out_arrow(310, 24.5, "accent")
        s.text(p["line"], "body", 13.5, 0, 57, "body")
        s.text(p["proof"], "mono", 11, 0, 79, "strong")
        dates(s, p, 0, 96, 10.5)
    if not first:  # the section heading above already draws a rule
        s.rule(0.5)
    if last:
        s.rule(s.h - 0.5)
    s.save(f"product-{p['slug']}-{'wide' if wide else 'narrow'}-{theme}.svg")


def method(line, theme, wide):
    if wide:
        s = Svg(line, 680, 140, theme, METHOD_ALT)
        col, y = 680 / 5, 14
        s.parts.append(f'<path d="M5 {y}H680" stroke="{s.c["line"]}" stroke-width="1.5"/>')
        for i, (name, lines, _, gated) in enumerate(STEPS):
            x = i * col
            if gated:
                s.gate(x - 18, y)
            s.node(x + 5, y)
            s.text(name, "InterDisplay-SemiBold", 17, x, 48, "strong", tracking=-0.015)
            for j, t in enumerate(lines):
                s.text(t, "body", 12.5, x, 70 + j * 18, "body")
        s.gate(7, 125, 5.5)
        s.text(KEY, "body", 12.5, 22, 129.5, "mute")
    else:
        s = Svg(line, 320, 348, theme, METHOD_ALT)
        tx, pitch, top = 7, 62, 12
        s.parts.append(f'<path d="M{tx} {top}V{top + 4 * pitch}" stroke="{s.c["line"]}" stroke-width="1.5"/>')
        for i, (name, _, text, gated) in enumerate(STEPS):
            y = top + i * pitch
            if gated:
                s.gate(tx, y - 24)
            s.node(tx, y)
            s.text(name, "InterDisplay-SemiBold", 17, 28, y + 6, "strong", tracking=-0.015)
            s.text(text, "body", 12, 28, y + 25, "body")
        ky = top + 4 * pitch + 62
        s.gate(tx, ky - 4, 5.5)
        s.text("Gate: the change waits here until", "body", 12, 28, ky, "mute")
        s.text("the step before it passes.", "body", 12, 28, ky + 17, "mute")
    s.save(f"method-{'wide' if wide else 'narrow'}-{theme}.svg")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand-src", required=True)
    ap.add_argument("--fonts", required=True)
    a = ap.parse_args()
    line = load_fonts(a.brand_src, a.fonts)
    for theme in THEMES:
        for wide in (True, False):
            for i, p in enumerate(PRODUCTS):
                product(line, p, theme, wide, i == 0, i == len(PRODUCTS) - 1)
            method(line, theme, wide)


if __name__ == "__main__":
    main()
