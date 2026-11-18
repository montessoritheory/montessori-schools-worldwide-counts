"""Builds images/cover.png and the charts from data/*.csv. Run from anywhere.
Needs pandas, numpy, matplotlib and Pillow. World outlines come from Natural Earth (public domain),
downloaded once into ../../_raw."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.patheffects as pe
from matplotlib.patches import Circle
import msf_style as S

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA, IMG, RAW = ROOT / "data", ROOT / "images", ROOT.parent / "_raw"
IMG.mkdir(exist_ok=True)

country = pd.read_csv(DATA / "by_country.csv")
region = pd.read_csv(DATA / "by_region.csv")
city = pd.read_csv(DATA / "by_city.csv")
summary = dict(pd.read_csv(DATA / "summary.csv").values)
total, n_cty, n_cities = int(summary["total_schools"]), int(summary["countries"]), int(summary["cities"])
n_regions, verified = int(summary["regions"]), int(summary["verified_schools"])
date = summary["directory_date"]
SRC = f"Source: Montessori School Finder directory, snapshot {date}. Counts of listings, not a census."
top5 = country.sort_values("schools", ascending=False).head(5).schools.sum() / total

# ---- cover
S.cover(IMG / "cover.png", HERE / "cover_photo.jpg", "Montessori Schools Worldwide\nCounts by Country, Region and City",
        "Open dataset  ·  CC BY 4.0", f"{total:,}", f"schools in the\ndirectory",
        [f"{n_cty} countries and UK nations", f"{n_regions} regions", f"{n_cities:,} cities"],
        "Photo: Anil Sharma, Pexels", accent=S.BLUE, focus=(0.0, 0.42), zoom=1.3, title_size=39)

# ---- key numbers
S.key_numbers(IMG / "key_numbers.png", "The Directory in Six Numbers", f"Aggregate counts only, no school records. Snapshot {date}.", SRC, [
    (f"{total:,}", "Montessori schools in the directory", S.BLUE),
    (f"{n_cty}", "countries and UK nations", S.TEAL),
    (f"{n_cities:,}", "cities with at least one school", S.GREEN),
    (f"{verified:,}", f"schools with the Verified Montessori status ({verified / total:.1%})".replace("%", " %"), S.AMBER),
    (f"{top5:.0%}", "of the directory sits in the five largest countries", S.CORAL),
    (f"{n_regions}", "regions, states and counties with a school", S.VIOLET),
], accent=S.BLUE)

# ---- world choropleth
world = S.World(S.natural_earth(RAW))
by_iso = country.groupby("iso2").schools.sum()  # the four UK nations share GB
bins = [1, 10, 50, 200, 600, 2000, 10 ** 6]
labels = ["1 to 9", "10 to 49", "50 to 199", "200 to 599", "600 to 1,999", "2,000 or more"]
pal = [S.mix(S.BLUE, "#ffffff", t) for t in (0.82, 0.62, 0.42, 0.2)] + [S.BLUE, "#1e3a8a"]
none = "#e7ecf3"


def shade(v):
    for i in range(len(labels)):
        if bins[i] <= v < bins[i + 1]:
            return pal[i]
    return none


p = S.Page("Montessori Schools Around the World",
           f"Schools listed per country. The four UK nations are added together on the map ({int(by_iso['GB'])} schools).",
           SRC, accent=S.BLUE, size=(1400, 880))
ax = p.axes(50, p.top - 10, 1300, p.bottom - p.top - 10)
world.draw(ax, lambda c, n: shade(by_iso.get(c, 0)) if by_iso.get(c, 0) else none, edge="white", lw=0.6)
small = {"SG": (103.82, 1.35), "GI": (-5.35, 36.14), "GP": (-61.55, 16.25), "MQ": (-61.0, 14.64), "PF": (-149.4, -17.7)}
for code, (lo, la) in small.items():
    x, y = world.point(lo, la)
    ax.add_patch(Circle((x, y), 0.03, fc=shade(by_iso[code]), ec="white", lw=0.8, zorder=4))
halo = [pe.withStroke(linewidth=3, foreground="white")]
for code, nm in [("US", None), ("IN", None), ("DE", None), ("IE", None), ("GB", None), ("CA", None), ("FR", None), ("PL", None), ("ZA", None)]:
    c = world.centroid(code, None)
    if c is None:
        continue
    dx, dy = {"GB": (-0.06, 0.1), "IE": (-0.2, 0.0), "DE": (0.12, -0.1), "FR": (-0.1, -0.12), "PL": (0.2, 0.08)}.get(code, (0, 0))
    ax.text(c[0] + dx, c[1] + dy, f"{by_iso[code]:,}", fontsize=11.5, fontweight="bold", ha="center", va="center", color=S.INK, path_effects=halo, zorder=6)
x0, y0 = 90, p.bottom - 24
for i, (lab, col) in enumerate(zip(labels, pal)):
    yy = y0 - (len(labels) - 1 - i) * 26
    S.rrect(p.ax, x0, yy - 9, 26, 18, r=4, fc=col, z=5)
    p.ax.text(x0 + 38, yy, lab, fontsize=12, va="center", color=S.INK, zorder=5)
p.ax.text(x0, y0 - 6 * 26 - 12, "Schools per country", fontsize=12.5, color=S.MUTED, zorder=5)
p.ax.text(p.W - 90, p.bottom - 20, "Small places such as Singapore are drawn as dots.", fontsize=11.5, color=S.MUTED, ha="right", va="center", zorder=5)
p.save(IMG / "world_map.png")

# ---- top countries lollipop, coloured by continent
cont = {"United States": "North America", "Canada": "North America", "India": "Asia", "Malaysia": "Asia", "Germany": "Europe", "Ireland": "Europe",
        "England": "Europe", "France": "Europe", "Poland": "Europe", "Italy": "Europe", "The Netherlands": "Europe", "Spain": "Europe",
        "South Africa": "Africa", "Australia": "Oceania", "New Zealand": "Oceania"}
ccol = {"North America": S.BLUE, "Europe": S.TEAL, "Asia": S.AMBER, "Africa": S.CORAL, "Oceania": S.VIOLET}
top = country.sort_values("schools", ascending=False).head(15)
p = S.Page("The 15 Countries With the Most Listed Montessori Schools",
           f"{total:,} schools in {n_cty} countries and UK nations. The top 15 hold {top.schools.sum() / total:.0%} of the directory.",
           SRC, accent=S.TEAL, size=(1400, 980))
ax = p.axes(250, p.top - 4, 980, p.bottom - p.top - 10)
S.lollipop(ax, top.country, list(top.schools), [ccol[cont[c]] for c in top.country], xmax=6600, size=260,
           note=lambda v: f"{v:,}  ({v / total:.1%})".replace("%", " %"))
for i, (k, c) in enumerate(ccol.items()):
    p.ax.scatter([930 + 0 * i], [p.top + 320 + i * 34], s=140, color=c, zorder=5)
    p.ax.text(952, p.top + 320 + i * 34, k, fontsize=13, va="center", zorder=5)
p.save(IMG / "top_countries.png")

# ---- US state tile grid
GRID = {"AK": (0, 0), "ME": (10, 0), "WI": (5, 1), "VT": (9, 1), "NH": (10, 1), "WA": (0, 2), "ID": (1, 2), "MT": (2, 2), "ND": (3, 2), "MN": (4, 2),
        "IL": (5, 2), "MI": (6, 2), "NY": (8, 2), "MA": (9, 2), "OR": (0, 3), "NV": (1, 3), "WY": (2, 3), "SD": (3, 3), "IA": (4, 3), "IN": (5, 3),
        "OH": (6, 3), "PA": (7, 3), "NJ": (8, 3), "CT": (9, 3), "RI": (10, 3), "CA": (0, 4), "UT": (1, 4), "CO": (2, 4), "NE": (3, 4), "MO": (4, 4),
        "KY": (5, 4), "WV": (6, 4), "VA": (7, 4), "MD": (8, 4), "DE": (9, 4), "AZ": (1, 5), "NM": (2, 5), "KS": (3, 5), "AR": (4, 5), "TN": (5, 5),
        "NC": (6, 5), "SC": (7, 5), "DC": (8, 5), "OK": (3, 6), "LA": (4, 6), "MS": (5, 6), "AL": (6, 6), "GA": (7, 6), "HI": (0, 7), "TX": (3, 7), "FL": (8, 7)}
us = region[region.country_code == "US"].set_index("region_code").schools
assert set(us.index) == set(GRID), set(us.index) ^ set(GRID)
ubins = [0, 25, 50, 100, 200, 500, 10 ** 5]
ulabels = ["Under 25", "25 to 49", "50 to 99", "100 to 199", "200 to 499", "500 or more"]
upal = [S.mix(S.GREEN, "#ffffff", t) for t in (0.88, 0.7, 0.5, 0.25)] + [S.GREEN, "#064e3b"]
p = S.Page("US Montessori Schools by State",
           f"{int(us.sum()):,} listed schools across 50 states and DC. One square per state, shaded by school count.",
           SRC, accent=S.GREEN, size=(1400, 1010))
ax = p.ax
cw_, ch_, gap = 102, 70, 6
gx, gy = 66 + (1268 - 11 * cw_ - 10 * gap) / 2, p.top + 6
for st, (cx, cy) in GRID.items():
    v = int(us[st])
    k = next(i for i in range(len(ulabels)) if ubins[i] <= v < ubins[i + 1])
    x, y = gx + cx * (cw_ + gap), gy + cy * (ch_ + gap)
    S.rrect(ax, x, y, cw_, ch_, r=12, fc=upal[k], z=3)
    light = k >= 4
    ax.text(x + cw_ / 2, y + 24, st, fontsize=15, fontweight="bold", ha="center", va="center", color="white" if light else S.INK, zorder=4)
    ax.text(x + cw_ / 2, y + 49, f"{v}", fontsize=13.5, ha="center", va="center", color="white" if light else S.INK, zorder=4)
ly = p.bottom - 14
for i, (lab, col) in enumerate(zip(ulabels, upal)):
    x = 66 + i * 195
    S.rrect(ax, x, ly - 11, 28, 22, r=5, fc=col, z=4)
    ax.text(x + 40, ly, lab, fontsize=12, va="center", zorder=4)
p.save(IMG / "top_us_states.png")

# ---- top cities, rounded bars
tc = city.sort_values(["schools", "city"], ascending=[False, True]).head(15)
p = S.Page("The 15 Cities With the Most Listed Montessori Schools",
           f"{n_cities:,} cities have at least one school. Each school is placed in the nearest GeoNames place.",
           SRC, accent=S.AMBER, size=(1400, 980))
ax = p.ax
row = (p.bottom - p.top - 4) / 15
vmax = tc.schools.max()
palette = [S.BLUE, S.TEAL, S.GREEN, S.AMBER, S.CORAL, S.VIOLET]
cc = {c: palette[i % len(palette)] for i, c in enumerate(tc.country.drop_duplicates())}
for i, (_, r) in enumerate(tc.iterrows()):
    y = p.top + 4 + i * row
    ax.text(66, y + row / 2, f"{i + 1}", fontsize=13, color=S.MUTED, va="center", fontweight="bold", zorder=4)
    ax.text(104, y + row / 2 - 8, r.city, fontsize=14.5, fontweight="bold", va="center", zorder=4)
    ax.text(104, y + row / 2 + 12, r.country, fontsize=11, color=S.MUTED, va="center", zorder=4)
    w = 60 + (780 * r.schools / vmax)
    S.rrect(ax, 400, y + 7, w, row - 14, r=(row - 14) / 2, fc=cc[r.country], z=3)
    ax.text(400 + w + 14, y + row / 2, f"{r.schools}", fontsize=14.5, fontweight="bold", va="center", zorder=4)
p.save(IMG / "top_cities.png")
print("images ok")
