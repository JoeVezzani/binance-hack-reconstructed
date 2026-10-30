"""Brand-dark matplotlib charts for the Meta outlook report (DESIGN.md marketing palette)."""
import os, datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import matplotlib.dates as mdates

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "charts")
os.makedirs(OUT, exist_ok=True)
for f in ("PlusJakartaSans-400.ttf", "PlusJakartaSans-600.ttf", "PlusJakartaSans-700.ttf"):
    fm.fontManager.addfont(os.path.join(HERE, "fonts", f))

CANVAS, CARD = "#0B121E", "#0D1522"
GREEN, BLUE, AMBER, RED = "#14B881", "#6EA6F8", "#F59E0B", "#FF8A8A"
WHITE, BODY, MUTED, GRID = "#FFFFFF", "#A0A5B8", "#6B7290", "#1B2433"
SERIES = [GREEN, BLUE, AMBER, "#C084FC", RED, "#4ADE80", "#94A3B8"]
NET = {"tweet": ("X", BLUE), "tiktok-video": ("TikTok", "#F472B6"), "youtube-video": ("YouTube", RED),
       "reddit-post": ("Reddit", AMBER), "instagram-post": ("Instagram", "#C084FC"), "news": ("News", "#94A3B8")}

plt.rcParams.update({
    "font.family": "Plus Jakarta Sans", "font.size": 9, "text.color": BODY, "axes.labelcolor": MUTED,
    "axes.edgecolor": GRID, "xtick.color": MUTED, "ytick.color": MUTED, "axes.facecolor": CARD,
    "figure.facecolor": CARD, "savefig.facecolor": CARD, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.titlecolor": WHITE, "axes.titlesize": 10, "axes.titleweight": 600, "axes.titlelocation": "left",
    "legend.frameon": False, "legend.fontsize": 8, "xtick.major.size": 0, "ytick.major.size": 0,
})

def human(n):
    n = float(n)
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(n) >= div:
            v = n / div
            return f"{v:.1f}{suf}" if v < 10 else f"{v:.0f}{suf}"
    return f"{n:.0f}"

def _save(fig, name):
    p = os.path.join(OUT, name + ".png")
    fig.savefig(p, dpi=220, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    return p

def hbar(name, labels, values, w=6.6, h=None, color=GREEN, fmt=lambda v: f"{v:.2f}", neg_color=RED, ref=None, xlabel=None, colors=None):
    h = h or max(1.6, 0.27 * len(labels) + 0.5)
    fig, ax = plt.subplots(figsize=(w, h))
    cols = colors or [color if v >= (ref if ref is not None else 0) else neg_color for v in values]
    y = range(len(labels))[::-1]
    ax.barh(list(y), values, color=cols, height=0.62, zorder=3)
    ax.set_yticks(list(y)); ax.set_yticklabels(labels, color=WHITE, fontsize=8.5)
    ax.grid(axis="y", visible=False)
    if ref is not None:
        ax.axvline(ref, color=MUTED, lw=0.8, ls=(0, (3, 3)), zorder=4)
    lo, hi = min(min(values), ref or 0), max(values)
    pad = (hi - lo) * 0.16 or 1
    ax.set_xlim(min(lo - pad * 0.15, 0 if lo >= 0 else lo - pad * 0.3), hi + pad)
    for yy, v in zip(y, values):
        base = ref if ref is not None else 0
        ax.text((v if v >= base else base) + pad * 0.04, yy, fmt(v), va="center",
                ha="left", color=WHITE if v >= base else RED, fontsize=7.5, fontweight=600, zorder=5)
    if xlabel: ax.set_xlabel(xlabel, fontsize=8)
    if max(abs(v) for v in values) >= 1e5: ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: human(x)))
    ax.tick_params(axis="x", labelsize=7.5)
    return _save(fig, name)

def lines(name, series, w=6.6, h=2.4, log=False, normalize=False, title=None, smooth=7):
    """series: list of (label, times[], values[])"""
    fig, ax = plt.subplots(figsize=(w, h))
    for i, (lab, t, v) in enumerate(series):
        d = [datetime.datetime.fromtimestamp(x, datetime.timezone.utc) for x in t]
        vv = list(v)
        if smooth and len(vv) > smooth:
            vv = [sum(vv[max(0, j - smooth + 1):j + 1]) / len(vv[max(0, j - smooth + 1):j + 1]) for j in range(len(vv))]
        if normalize:
            base = sum(vv[:30]) / 30 if len(vv) >= 30 and sum(vv[:30]) > 0 else (max(vv) or 1)
            vv = [x / base * 100 for x in vv]
        ax.plot(d, vv, color=SERIES[i % len(SERIES)], lw=1.6, label=lab, zorder=3)
    if log: ax.set_yscale("log")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: human(x)))
    ax.tick_params(labelsize=7.5)
    if normalize: ax.axhline(100, color=MUTED, lw=0.7, ls=(0, (3, 3)))
    if title: ax.set_title(title)
    if normalize: ax.set_ylabel("Share-of-voice index (start = 100)", fontsize=7)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, labelcolor=BODY, handlelength=1.2, fontsize=7.2)
    return _save(fig, name)

def network_stack(name, rows, w=6.6, h=None):
    """rows: list of (label, {type: interactions}) -> 100% stacked bars of interaction share."""
    h = h or max(1.6, 0.3 * len(rows) + 0.7)
    fig, ax = plt.subplots(figsize=(w, h))
    order = ["tweet", "tiktok-video", "youtube-video", "instagram-post", "reddit-post", "news"]
    y = list(range(len(rows)))[::-1]
    left = [0.0] * len(rows)
    for t in order:
        vals = []
        for _, d in rows:
            tot = sum((d or {}).values()) or 1
            vals.append(100 * (d or {}).get(t, 0) / tot)
        ax.barh(y, vals, left=left, color=NET[t][1], height=0.62, label=NET[t][0], zorder=3)
        for yy, l, v in zip(y, left, vals):
            if v >= 9:
                ax.text(l + v / 2, yy, f"{v:.0f}%", ha="center", va="center", fontsize=6.8, color=CANVAS, fontweight=700, zorder=4)
        left = [a + b for a, b in zip(left, vals)]
    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], color=WHITE, fontsize=8.5)
    ax.set_xlim(0, 100); ax.grid(False); ax.set_xticks([])
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=6, labelcolor=BODY, handlelength=1, fontsize=7.5)
    return _save(fig, name)

def scatter(name, pts, w=6.6, h=3.6, xlabel="", ylabel="", logx=True, ref_y=None):
    """pts: list of (label, x, y, color)"""
    fig, ax = plt.subplots(figsize=(w, h))
    for lab, x, yv, c in pts:
        ax.scatter([x], [yv], s=28, color=c, zorder=3, edgecolors=CARD, linewidths=0.6)
        ax.annotate(lab, (x, yv), xytext=(4, 3), textcoords="offset points", fontsize=6.8, color=WHITE, zorder=4)
    if logx: ax.set_xscale("log")
    if ref_y is not None: ax.axhline(ref_y, color=MUTED, lw=0.7, ls=(0, (3, 3)))
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: human(x)))
    ax.set_xlabel(xlabel, fontsize=8); ax.set_ylabel(ylabel, fontsize=8); ax.tick_params(labelsize=7.5)
    return _save(fig, name)

def vbars(name, labels, values, w=6.6, h=2.4, colors=None, fmt=human, title=None):
    fig, ax = plt.subplots(figsize=(w, h))
    x = range(len(labels))
    ax.bar(list(x), values, color=colors or GREEN, width=0.62, zorder=3)
    ax.set_xticks(list(x)); ax.set_xticklabels(labels, fontsize=7.5, color=WHITE)
    ax.grid(axis="x", visible=False)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: fmt(v)))
    for xx, v in zip(x, values):
        ax.text(xx, v, fmt(v), ha="center", va="bottom", fontsize=7, color=WHITE, fontweight=600)
    if title: ax.set_title(title)
    return _save(fig, name)
