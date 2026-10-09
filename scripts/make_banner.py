"""Draw docs/img/banner.svg: the README banner. Rivers and lights in the page's own visual language.

Deterministic (fixed seed); no external fonts or images, so it renders the same on GitHub as locally.
"""
import math, os, random

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1280, 360
RIVERS = [("#3987e5", 118, [10, 12, 15, 20, 17, 21, 27, 30, 14]), ("#d95926", 176, [3, 4, 6, 9, 10, 12, 14, 13, 6]),
          ("#199e70", 222, [2, 3, 3, 5, 7, 9, 12, 14, 7]), ("#9085e9", 262, [1, 2, 3, 3, 4, 6, 8, 11, 6]), ("#d55181", 298, [1, 1, 2, 3, 3, 4, 5, 7, 3])]
rng = random.Random(2018)


def curve(points):
    out = [f"M{points[0][0]:.1f},{points[0][1]:.1f}"]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        mid = (x0 + x1) / 2
        out.append(f"C{mid:.1f},{y0:.1f} {mid:.1f},{y1:.1f} {x1:.1f},{y1:.1f}")
    return " ".join(out)


parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Accelerator Phylogeny">',
         '<defs><radialGradient id="g" cx="24%" cy="0%" r="90%"><stop offset="0" stop-color="#12264a"/><stop offset="0.6" stop-color="#060913"/></radialGradient>'
         '<linearGradient id="t" x1="0" x2="1"><stop offset="0" stop-color="#eef3ff"/><stop offset="0.55" stop-color="#62e0ff"/><stop offset="1" stop-color="#9085e9"/></linearGradient>'
         '<filter id="glow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="3.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>',
         f'<rect width="{W}" height="{H}" fill="url(#g)"/>']
for x in range(0, W, 56):
    parts.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}" stroke="#223052" stroke-width="1" opacity="0.35"/>')
for y in range(0, H, 56):
    parts.append(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="#223052" stroke-width="1" opacity="0.35"/>')
left, right = 470, W - 30
xs = [left + (right - left) * i / 8 for i in range(9)]
lights = []
for colour, mid, widths in RIVERS:
    upper = [(x, mid - w * 0.55) for x, w in zip(xs, widths)]
    lower = [(x, mid + w * 0.55) for x, w in zip(xs, widths)]
    back = list(reversed(lower))
    fill = curve(upper) + f" L{back[0][0]:.1f},{back[0][1]:.1f} " + curve(back).split(" ", 1)[1] + " Z"
    parts.append(f'<path d="{fill}" fill="{colour}" opacity="0.22"/>')
    parts.append(f'<path d="{curve(upper)}" fill="none" stroke="{colour}" stroke-width="1.3" opacity="0.8"/>')
    parts.append(f'<path d="{curve(lower)}" fill="none" stroke="{colour}" stroke-width="1.3" opacity="0.8"/>')
    for x, w in zip(xs, widths):
        for _ in range(max(1, w // 4)):
            lights.append((x + rng.uniform(-26, 26), mid + rng.uniform(-w * 0.42, w * 0.42), rng.choice([2.2, 2.6, 3.2, 4.4]), colour))
for _ in range(26):                       # threads between lights of neighbouring years
    a, b = rng.sample(lights, 2)
    if 40 < abs(a[0] - b[0]) < 240:
        mid = (a[0] + b[0]) / 2
        parts.append(f'<path d="M{a[0]:.1f},{a[1]:.1f} C{mid:.1f},{a[1]:.1f} {mid:.1f},{b[1]:.1f} {b[0]:.1f},{b[1]:.1f}" fill="none" stroke="#62e0ff" stroke-width="0.9" opacity="0.32"/>')
for x, y, r, colour in lights:
    glow = ' filter="url(#glow)"' if r > 4 else ""
    parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{colour}" stroke="#060913" stroke-width="0.8"{glow}/>')
for i, x in enumerate(xs):
    parts.append(f'<text x="{x:.1f}" y="62" text-anchor="middle" font-family="ui-monospace,Menlo,Consolas,monospace" font-size="12" letter-spacing="2" fill="#6f7da0">{2018 + i}</text>')
font = "'Segoe UI',system-ui,-apple-system,Helvetica,Arial,sans-serif"
parts += [f'<text x="48" y="118" font-family="{font}" font-size="13" font-weight="600" letter-spacing="5" fill="#62e0ff">THE EVOLUTIONARY TREE OF AI ACCELERATORS</text>',
          f'<text x="46" y="182" font-family="{font}" font-size="56" font-weight="800" letter-spacing="1" fill="url(#t)">ACCELERATOR</text>',
          f'<text x="46" y="240" font-family="{font}" font-size="56" font-weight="800" letter-spacing="1" fill="url(#t)">PHYLOGENY</text>',
          f'<text x="48" y="282" font-family="{font}" font-size="16" fill="#aab6d3">Every paper a light. Every citation a thread.</text>',
          f'<text x="48" y="306" font-family="{font}" font-size="16" fill="#aab6d3">Every product a marker on the same time axis.</text>', "</svg>"]
os.makedirs(os.path.join(REPO, "docs", "img"), exist_ok=True)
open(os.path.join(REPO, "docs", "img", "banner.svg"), "w").write("\n".join(parts) + "\n")
print(f"banner.svg: {len(lights)} lights, {sum(len(p) for p in parts) // 1024} KB")
