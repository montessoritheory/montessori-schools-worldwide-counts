"""Builds images/cover.png and three charts from data/*.csv. Run from anywhere.
Needs pandas and matplotlib."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parent.parent
DATA, IMG = ROOT / "data", ROOT / "images"
IMG.mkdir(exist_ok=True)

INK, BLUE, GREEN, MUTED = "#0f172a", "#2563eb", "#059669", "#64748b"
BG, MINT, LINE = "#f8fafc", "#ecfdf5", "#e2e8f0"
have = {f.name for f in font_manager.fontManager.ttflist}
plt.rcParams["font.family"] = next((f for f in ["Segoe UI", "Inter", "Arial", "DejaVu Sans"] if f in have), "DejaVu Sans")

country = pd.read_csv(DATA / "by_country.csv")
region = pd.read_csv(DATA / "by_region.csv")
city = pd.read_csv(DATA / "by_city.csv")
summary = dict(pd.read_csv(DATA / "summary.csv").values)
total, n_cty, n_cities = int(summary["total_schools"]), int(summary["countries"]), int(summary["cities"])
date = summary["directory_date"]
FOOT = "Montessori School Finder × Montessori Theory"


def card(ax, x, y, w, h, fc, ec=LINE, r=0.02):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=1.5, transform=ax.transAxes))


def cover():
    fig = plt.figure(figsize=(16, 8), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); fig.patch.set_facecolor(BG)
    card(ax, 0.03, 0.06, 0.94, 0.88, "white", r=0.025)
    ax.add_patch(FancyBboxPatch((0.03, 0.06), 0.012, 0.88, boxstyle="round,pad=0,rounding_size=0.006", fc=BLUE, ec="none", transform=ax.transAxes))
    ax.text(0.075, 0.84, "OPEN DATASET  ·  CC BY 4.0", color=GREEN, fontsize=15, fontweight="bold", va="center")
    ax.text(0.075, 0.69, "Montessori Schools Worldwide", color=INK, fontsize=46, fontweight="bold", va="center")
    ax.text(0.075, 0.58, "Counts by Country, Region and City", color=BLUE, fontsize=30, fontweight="bold", va="center")
    tiles = [(f"{total:,}", "schools in the directory"), (f"{n_cty}", "countries and UK nations"), (f"{n_cities:,}", "cities with a page")]
    x = 0.075
    for big, small in tiles:
        card(ax, x, 0.20, 0.265, 0.24, MINT if big == f"{total:,}" else BG, r=0.02)
        ax.text(x + 0.02, 0.35, big, color=GREEN if big == f"{total:,}" else INK, fontsize=40, fontweight="bold", va="center")
        ax.text(x + 0.02, 0.255, small, color=MUTED, fontsize=15, va="center")
        x += 0.29
    ax.text(0.075, 0.115, f"Aggregate counts only, no school records. Directory snapshot {date}.", color=MUTED, fontsize=13, va="center")
    ax.text(0.925, 0.115, FOOT, color=INK, fontsize=13, fontweight="bold", va="center", ha="right")
    fig.savefig(IMG / "cover.png", dpi=100, facecolor=BG)
    plt.close(fig)


def barchart(df, label, value, title, sub, fname, color=BLUE, hi=None):
    df = df.iloc[::-1]
    fig, ax = plt.subplots(figsize=(12, 7.2), dpi=120)
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    cols = [GREEN if (hi and l == hi) else color for l in df[label]]
    bars = ax.barh(df[label], df[value], color=cols, height=0.68)
    for b, v in zip(bars, df[value]):
        ax.text(b.get_width() + df[value].max() * 0.01, b.get_y() + b.get_height() / 2, f"{v:,}", va="center", color=INK, fontsize=11, fontweight="bold")
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(LINE)
    ax.tick_params(axis="y", length=0, labelsize=12, labelcolor=INK)
    ax.tick_params(axis="x", colors=MUTED, labelsize=10)
    ax.xaxis.grid(True, color=LINE, lw=1); ax.set_axisbelow(True)
    ax.set_xlim(0, df[value].max() * 1.12)
    fig.text(0.04, 0.94, title, fontsize=20, fontweight="bold", color=INK, va="center")
    fig.text(0.04, 0.89, sub, fontsize=12, color=MUTED, va="center")
    fig.text(0.04, 0.03, f"Source: Montessori School Finder directory, snapshot {date}. Counts of listings, not a census.", fontsize=9.5, color=MUTED)
    fig.text(0.96, 0.03, FOOT, fontsize=9.5, color=INK, fontweight="bold", ha="right")
    fig.subplots_adjust(left=0.28, right=0.96, top=0.85, bottom=0.1)
    fig.savefig(IMG / fname, facecolor=BG)
    plt.close(fig)


cover()
top = country.sort_values("schools", ascending=False).head(15)
barchart(top, "country", "schools", "The 15 Countries With the Most Listed Montessori Schools",
         f"{total:,} schools in {n_cty} countries and UK nations. The top 15 hold {top.schools.sum() / total:.0%} of the directory.", "top_countries.png", hi="United States")
us = region[region.country_code == "US"].sort_values("schools", ascending=False).head(15)
barchart(us, "region", "schools", "The 15 US States With the Most Listed Montessori Schools",
         f"{int(region[region.country_code == 'US'].schools.sum()):,} US schools across 50 states and DC.", "top_us_states.png", color=GREEN)
tc = city.sort_values(["schools", "city"], ascending=[False, True]).head(15).copy()
tc["label"] = tc.city + ", " + tc.country
barchart(tc, "label", "schools", "The 15 Cities With the Most Listed Montessori Schools",
         f"{n_cities:,} cities have at least one school. Each school is placed in the nearest GeoNames place.", "top_cities.png")
print(top[["country", "schools"]].head(5).to_string(), us[["region", "schools"]].head(5).to_string(), tc[["label", "schools"]].head(5).to_string())
