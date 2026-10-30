#!/usr/bin/env python3
"""v2 reconstruction charts (additive to build_charts.py): master Gantt, night Gantt, detection lag,
freeze ladder, cover art + cover glow. Every timestamp is UTC and comes from chapters/forensics.json,
FACTS.md or synthesis.json timeline (verified in v1). Outputs into build/charts/ under new names."""
import os, json, datetime as dt
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import matplotlib.text as _mtext
_text_init = _mtext.Text.__init__
def _text_init_nocalt(self, *a, **k):  # Plus Jakarta's contextual alternates turn "0x" into "0×"; keep it literal
    _text_init(self, *a, **k); self.set_fontfeatures(["-calt"])
_mtext.Text.__init__ = _text_init_nocalt
import matplotlib.dates as mdates
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); OUT = os.path.join(HERE, "charts")
for f in ("PlusJakartaSans-400.ttf", "PlusJakartaSans-500.ttf", "PlusJakartaSans-600.ttf", "PlusJakartaSans-700.ttf", "PlusJakartaSans-800.ttf"):
    fm.fontManager.addfont(os.path.join(HERE, "fonts", f))
CANVAS = "#0B121E"; CARD = "#0D1522"; GRID = "#1A2433"; WHITE = "#FFFFFF"; BODY = "#A9AEC0"; MUTED = "#69718C"
GREEN, BLUE, AMBER, RED, VIOLET, SLATE = "#14B881", "#6EA6F8", "#F2A93B", "#FF7A7A", "#B794F6", "#7C8599"
LANE = {"fund": SLATE, "prep": BLUE, "attack": RED, "issuer": GREEN, "binance": AMBER, "social": VIOLET, "market": "#5B6478", "other": "#E88BB5"}
plt.rcParams.update({"text.parse_math": False, "font.family": "Plus Jakarta Sans", "font.size": 8, "text.color": BODY, "axes.facecolor": CARD, "figure.facecolor": CARD,
                     "savefig.facecolor": CARD, "axes.edgecolor": GRID, "xtick.color": MUTED, "ytick.color": MUTED, "axes.labelcolor": MUTED,
                     "xtick.major.size": 0, "ytick.major.size": 0, "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False, "axes.spines.bottom": False})
UTC = dt.timezone.utc
def T(s):
    """'10-29 20:20:59' or '10-29 20:20' -> datetime (2026, UTC)."""
    d, t = s.split(); m, dd = d.split("-"); p = [int(x) for x in t.split(":")] + [0]
    return dt.datetime(2026, int(m), int(dd), p[0], p[1], p[2], tzinfo=UTC)
def save(fig, name, transparent=False):
    p = os.path.join(OUT, name + ".png"); fig.savefig(p, dpi=260, bbox_inches="tight", pad_inches=0.10, transparent=transparent); plt.close(fig); return p

# ---------------------------------------------------------------- event model
SETUP = [  # (lane, start, end_or_None, label)
    ("fund", "10-28 07:39", None, "Tornado 0.1 ETH"), ("fund", "10-28 08:53", None, "Tornado 0.1 ETH"),
    ("fund", "10-29 01:15", None, "sibling funded"), ("fund", "10-29 07:08", None, "sibling funded"), ("fund", "10-29 08:23", None, "Tornado 0.1 ETH"), ("fund", "10-29 14:54", None, "1 ETH pool"),
    ("prep", "10-29 02:28:59", None, "sweeper v1 deployed"), ("prep", "10-29 13:51:35", "10-29 14:24:11", "rehearsal 1"),
    ("prep", "10-29 15:59:11", None, "sweeper v2 deployed"), ("prep", "10-29 16:20:47", "10-29 16:47:23", "rehearsal 2"), ("fund", "10-29 18:20:47", None, "gas 1.08 ETH"),
]
NIGHT = {
    "attack": [("10-29 20:20:59", None, "Delegation: 50 signed authorizations"), ("10-29 20:24:23", None, "Sweep: 167,464 ETH + 63 tokens"),
               ("10-29 20:41:23", None, "780M USDC via Hot Wallet 34"), ("10-29 20:59:47", None, "43M USDC"), ("10-29 21:04", None, "re-sweep"),
               ("10-29 21:44", None, "re-sweep 200.4M USDT"), ("10-29 22:39", None, "long-tail basket"), ("10-29 23:36", "10-29 23:56", "6 empty sweeps")],
    "other": [("10-29 20:06", None, "XRP $236M out*"), ("10-29 20:11", None, "SOL $95M out*")],
    "issuer": [("10-29 21:05", None, "Tether $971M (first report)"), ("10-29 21:18", None, "Circle >800M USDC"), ("10-29 21:25", None, "Tether 1.567B USDT"),
               ("10-29 22:22", None, "WLFI $27M USD1")],
    "binance": [("10-29 22:08", None, "thanks Ripple"), ("10-29 21:15", None, "CZ: 'looks like a hack'"), ("10-29 21:29", None, "'funds completely safe'"), ("10-29 22:32", None, "partial withdrawals"),
                ("10-29 23:06", None, "Alpha paused"), ("10-29 23:22", None, "$2.54B verified frozen"), ("10-30 00:10:35", None, "revokes delegation"),
                ("10-30 00:13", None, "all D/W paused"), ("10-30 00:52", None, "~$3B frozen")],
    "social": [("10-29 20:32", None, "first 'hack' post (+8 min)"), ("10-29 20:54", None, "mechanism explained"), ("10-29 21:09", None, "full reconstruction"),
               ("10-29 21:31", None, "rehearsal found"), ("10-29 21:42", None, "'$5.6B stolen'"), ("10-29 22:33", None, "Musk: 'Everyday is Zeroday'")],
    "market": [("10-29 20:50", None, "BNB low $692"), ("10-29 21:00", None, "BTC low $78.8K")],
}
WINDOW = (T("10-29 20:20:59"), T("10-30 00:10:35"))
LANE_NAME = {"fund": "Funding", "prep": "Build and rehearse", "attack": "Attacker on Binance 14", "other": "Other chains*", "issuer": "Issuer freezes",
             "binance": "Binance", "social": "Social", "market": "Market"}

def place_labels(ax, items, y, color, x0, x1, width_in, tiers=3, fs=6.4, dy=0.24, first_up=True):
    """Draw markers + labels in up to `tiers` alternating rows without overlap (greedy)."""
    span = (x1 - x0).total_seconds(); inch_per_sec = width_in / span; char_in = fs * 0.55 / 72
    last_end = {}
    for (s, e, lab) in sorted(items, key=lambda r: T(r[0])):
        ts = T(s)
        if e: ax.plot([ts, T(e)], [y, y], color=color, lw=4.5, solid_capstyle="round", zorder=4)
        else: ax.scatter([ts], [y], s=22, color=color, zorder=5, edgecolors=CARD, linewidths=0.8)
        w = len(lab) * char_in / inch_per_sec
        order = [0, 1, -1, 2, -2][:tiers] if first_up else [0, -1, 1, -2, 2][:tiers]
        slot = None
        for k in order:
            if last_end.get(k, x0 - dt.timedelta(days=9)) < ts - dt.timedelta(seconds=40 / inch_per_sec / 72 * 2):
                slot = k; break
        if slot is None: slot = min(last_end, key=lambda k: last_end[k])
        last_end[slot] = ts + dt.timedelta(seconds=w + 6 / 72 / inch_per_sec)
        yy = y + (0.0 if slot == 0 else slot * dy) + 0.13
        if slot != 0: ax.plot([ts, ts], [y + (0.06 if slot > 0 else -0.06), yy - 0.05 if slot > 0 else yy + 0.09], color=color, lw=0.5, alpha=0.55, zorder=3)
        ax.text(ts, yy, lab, fontsize=fs, color=WHITE, ha="left", va="bottom" if slot >= 0 else "top", zorder=6,
                bbox=dict(boxstyle="round,pad=0.12", fc=CARD, ec="none", alpha=0.85))

# ---------------------------------------------------------------- 1. master gantt (broken axis)
def master():
    fig = plt.figure(figsize=(7.4, 3.9)); gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.25], wspace=0.04)
    a1 = fig.add_subplot(gs[0]); a2 = fig.add_subplot(gs[1], sharey=a1)
    lanes = ["fund", "prep", "attack", "issuer", "binance", "social"]; Y = {k: len(lanes) - i for i, k in enumerate(lanes)}
    L1, R1 = T("10-28 06:00"), T("10-29 20:00"); L2, R2 = T("10-29 20:00"), T("10-30 01:05")
    for ax, (l, r) in ((a1, (L1, R1)), (a2, (L2, R2))):
        ax.set_xlim(l, r); ax.set_ylim(0.35, len(lanes) + 0.75); ax.grid(axis="x", color=GRID, lw=0.6); ax.grid(axis="y", visible=False)
        for k, y in Y.items(): ax.axhline(y, color=GRID, lw=0.6, zorder=1)
    # left panel: setup
    for lane, s, e, lab in SETUP:
        y = Y[lane]; c = LANE[lane]
        if e: a1.plot([T(s), T(e)], [y, y], color=c, lw=6, solid_capstyle="round", zorder=4)
        else: a1.scatter([T(s)], [y], s=20, color=c, zorder=5, edgecolors=CARD, linewidths=0.7)
    a1.annotate("sweeper v1", (T("10-29 02:28:59"), Y["prep"]), xytext=(-4, 8), textcoords="offset points", fontsize=6.2, color=WHITE, ha="right")
    a1.annotate("2 rehearsals", (T("10-29 15:00"), Y["prep"]), xytext=(0, 8), textcoords="offset points", fontsize=6.2, color=WHITE, ha="center")
    a1.annotate("Tornado Cash funding", (T("10-28 08:15"), Y["fund"]), xytext=(0, 8), textcoords="offset points", fontsize=6.2, color=WHITE, ha="left")
    a1.text(T("10-28 21:00"), Y["social"], "no public post about any of it", fontsize=6.3, color=MUTED, ha="center", va="center", style="italic")
    a1.text(T("10-28 21:00"), Y["attack"], "Binance 14 operating normally", fontsize=6.3, color=MUTED, ha="center", va="center", style="italic")
    a1.xaxis.set_major_locator(matplotlib.ticker.FixedLocator([mdates.date2num(T(x)) for x in ("10-28 06:00", "10-28 18:00", "10-29 06:00")])); a1.xaxis.set_major_formatter(mdates.DateFormatter("%b %d\n%H:%M"))
    # right panel: night
    a2.axvspan(*WINDOW, color=RED, alpha=0.07, zorder=0, lw=0)
    a2.plot(list(WINDOW), [Y["attack"]] * 2, color=RED, lw=6, alpha=0.30, solid_capstyle="round", zorder=3)
    for lane in ("attack", "issuer", "binance", "social"):
        for s, e, lab in NIGHT[lane]:
            if e: a2.plot([T(s), T(e)], [Y[lane]] * 2, color=LANE[lane], lw=6, solid_capstyle="round", zorder=4)
            else: a2.scatter([T(s)], [Y[lane]], s=20, color=LANE[lane], zorder=5, edgecolors=CARD, linewidths=0.7)
    a2.text(T("10-29 22:15"), Y["attack"] + 0.30, "attacker code live on Binance 14: 3h 49m", fontsize=6.3, color=RED, ha="center")
    a2.text(T("10-29 20:22"), Y["prep"] + 0.0, "drain begins 20:24", fontsize=6.3, color=WHITE, ha="left", va="center")
    a2.text(T("10-29 21:05"), Y["issuer"] + 0.30, "freezes start 21:05", fontsize=6.2, color=GREEN, ha="left")
    a2.text(T("10-29 21:15"), Y["binance"] + 0.30, "first word 21:15", fontsize=6.2, color=AMBER, ha="left")
    a2.text(T("10-29 20:32"), Y["social"] + 0.30, "crowd has it 20:32", fontsize=6.2, color=VIOLET, ha="left")
    a2.xaxis.set_major_locator(mdates.HourLocator()); a2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    plt.setp(a2.get_yticklabels(), visible=False)
    a1.set_yticks([Y[k] for k in lanes]); a1.set_yticklabels([LANE_NAME[k] for k in lanes], fontsize=7.2, color=WHITE)
    for ax in (a1, a2): ax.tick_params(axis="x", labelsize=6.4)
    # break marks + panel titles
    a1.set_title("Setup: Oct 28 06:00 to Oct 29 20:00", fontsize=8, color=MUTED, loc="left", pad=6, fontweight=600)
    a2.set_title("The attack night, 20:00 to 01:00 (about 9.5x scale)", fontsize=8, color=MUTED, loc="left", pad=6, fontweight=600)
    for ax, xs in ((a1, 1.0), (a2, 0.0)):
        ax.plot([xs, xs], [0, 1], transform=ax.transAxes, color=MUTED, lw=0.8, ls=(0, (2, 2)), clip_on=False)
    return save(fig, "g_master_gantt")

# ---------------------------------------------------------------- 2. the night, lane by lane, with engagement strip
NIGHT_PLACED = {  # (start, end, label, tier, ha): tiers +-1/+-2 hand-placed so no label collides at 7.4in
    "other": [("10-29 20:05", None, "XRP $236M*", 1, "left"), ("10-29 20:10:18", None, "SOL $95M*", -1, "left")],
    "attack": [("10-29 20:20:59", None, "20:21 delegation", 2, "left"), ("10-29 20:24:23", None, "20:24 sweep 167K ETH, 63 tokens", 1, "left"),
               ("10-29 20:41:23", None, "20:41  780M USDC", -1, "left"), ("10-29 20:59:47", None, "20:59 43M USDC", -2, "left"),
               ("10-29 21:44", None, "21:44 re-sweep 200.4M USDT", 1, "left"), ("10-29 22:39", None, "22:39 long-tail sweep", -1, "left"),
               ("10-29 23:36", "10-29 23:56", "6 empty sweeps", 1, "left")],
    "issuer": [("10-29 21:05", None, "Tether $971M", 1, "left"), ("10-29 21:18", None, "Circle 800M+ USDC", -2, "left"), ("10-29 21:25", None, "Tether to $1.567B", -1, "left"),
               ("10-29 22:22", None, "WLFI $27M", -1, "left")],
    "binance": [("10-29 21:15", None, "CZ: looks like a hack", 1, "left"), ("10-29 21:29", None, "'funds completely safe'", -1, "left"), ("10-29 22:32", None, "partial withdrawals", 2, "left"),
                ("10-29 22:08", None, "", 1, "left"), ("10-29 23:06", None, "Alpha paused", -2, "left"), ("10-29 23:22", None, "$2.54B verified frozen", 1, "left"), ("10-30 00:10:35", None, "00:10 revokes delegation", -1, "right"),
                ("10-30 00:13", None, "all deposits paused", 2, "left"), ("10-30 00:52", None, "~$3B frozen", 1, "left")],
    "social": [("10-29 20:32", None, "20:32 first 'hack' post", 1, "left"), ("10-29 20:54", None, "mechanism explained", -2, "left"), ("10-29 21:09", None, "full reconstruction", -1, "left"),
               ("10-29 21:31", None, "rehearsal found", 2, "left"), ("10-29 21:42", None, "@WatcherGuru: '$5.6B stolen'", 1, "left"), ("10-29 22:33", None, "Musk: 'Everyday is Zeroday'", -1, "left")],
    "market": [("10-29 20:50", None, "BNB low $692", 1, "left"), ("10-29 21:00", None, "BTC low $78.8K", -1, "left")],
}
def night():
    A = json.load(open(os.path.join(ROOT, "analysis.json")))
    fig = plt.figure(figsize=(7.4, 6.0)); gs = fig.add_gridspec(2, 1, height_ratios=[5.0, 1.0], hspace=0.06)
    ax = fig.add_subplot(gs[0]); sx = fig.add_subplot(gs[1], sharex=ax)
    lanes = ["other", "attack", "issuer", "binance", "social", "market"]; Y = {k: (len(lanes) - i) * 1.0 for i, k in enumerate(lanes)}
    L, R = T("10-29 20:00"), T("10-30 01:24"); ax.set_xlim(L, R); ax.set_ylim(0.4, len(lanes) + 0.65)
    ax.axvspan(*WINDOW, color=RED, alpha=0.055, lw=0, zorder=0); ax.grid(axis="x", color=GRID, lw=0.6); ax.grid(axis="y", visible=False)
    for k, y in Y.items(): ax.axhline(y, color=GRID, lw=0.6, zorder=1)
    ax.plot(list(WINDOW), [Y["attack"]] * 2, color=RED, lw=5, alpha=0.22, solid_capstyle="round", zorder=2)
    OFF = {1: 0.20, 2: 0.40, -1: -0.20, -2: -0.40}
    for lane in lanes:
        c = LANE[lane]; y = Y[lane]
        for s, e, lab, tier, ha in NIGHT_PLACED[lane]:
            ts = T(s)
            if e: ax.plot([ts, T(e)], [y, y], color=c, lw=4.5, solid_capstyle="round", zorder=4)
            else: ax.scatter([ts], [y], s=20, color=c, zorder=5, edgecolors=CARD, linewidths=0.8)
            yy = y + OFF[tier]
            if not lab: continue
            ax.plot([ts, ts], [y + (0.05 if tier > 0 else -0.05), yy], color=c, lw=0.55, alpha=0.6, zorder=3)
            ax.text(ts + (dt.timedelta(minutes=1) if ha == "left" else -dt.timedelta(minutes=1)), yy, lab, fontsize=6.3, color=WHITE, ha=ha, va="center", zorder=6)
    ax.text(T("10-29 22:50"), Y["attack"] - 0.40, "attacker code live on Binance 14: 3h 49m", fontsize=6.3, color=RED, ha="center", va="center")
    ax.set_yticks([Y[k] for k in lanes]); ax.set_yticklabels([LANE_NAME[k] for k in lanes], fontsize=7.2, color=WHITE)
    plt.setp(ax.get_xticklabels(), visible=False)
    pre = A["binance_hourly"]["pre_series"]
    hrs = [(dt.datetime.fromtimestamp(r[0], UTC), r[1]) for r in pre if T("10-29 20:00").timestamp() <= r[0] < T("10-30 01:00").timestamp()]
    sx.bar([h + dt.timedelta(minutes=30) for h, _ in hrs], [v / 1e6 for _, v in hrs], width=0.034, color=VIOLET, alpha=0.8, zorder=3)
    for h, v in hrs: sx.text(h + dt.timedelta(minutes=30), v / 1e6 + 1.2, f"{v / 1e6:.1f}M", ha="center", fontsize=6.0, color=WHITE)
    sx.set_ylim(0, max(v for _, v in hrs) / 1e6 * 1.4); sx.set_yticks([]); sx.grid(False)
    sx.set_ylabel("Binance-topic\nengagements\nper hour", fontsize=6.3, rotation=0, ha="right", va="center", color=WHITE, labelpad=6)
    sx.xaxis.set_major_locator(mdates.MinuteLocator(byminute=[0, 30])); sx.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M")); sx.tick_params(axis="x", labelsize=6.4)
    return save(fig, "g_night_gantt")

# ---------------------------------------------------------------- 3. detection lag: chain event -> first public description
LAG = [  # step, chain time, first public, who
    ("Tornado Cash funding", "10-28 07:39", "10-29 20:32", "@spreekaway"), ("Sweeper v1 deployed", "10-29 02:28:59", "10-29 21:31", "@MetaFinancialAI"),
    ("Rehearsal 1", "10-29 13:51:35", "10-29 21:31", "@MetaFinancialAI"), ("Sweeper v2 deployed", "10-29 15:59:11", "10-29 21:09", "@0xQuit"),
    ("Rehearsal 2", "10-29 16:20:47", "10-29 21:31", "@MetaFinancialAI"), ("Delegation to Binance 14", "10-29 20:20:59", "10-29 20:54", "@odysseas_eth"),
    ("50 authorizations", "10-29 20:20:59", "10-29 21:21", "@0xQuit"), ("Sweep of Binance 14", "10-29 20:24:23", "10-29 20:32", "@spreekaway"),
    ("780M USDC pull", "10-29 20:41:23", "10-29 20:48", "@0xfoobar"), ("Revocation", "10-30 00:10:35", "10-30 00:44", "ChainCatcher"),
]
def fmt_lag(m):
    return f"{m:.0f} min" if m < 61 else (f"{m / 60:.1f} h" if m < 600 else f"{m / 60:.0f} h")
def lag():
    rows = [(s, (T(b) - T(a)).total_seconds() / 60, who, T(a)) for s, a, b, who in LAG]
    fig, ax = plt.subplots(figsize=(7.4, 3.5)); y = list(range(len(rows)))[::-1]
    for yy, (s, m, who, t0) in zip(y, rows):
        pre = t0 < T("10-29 20:20")
        c = BLUE if pre else RED
        ax.plot([1, m], [yy, yy], color=c, lw=2.2, alpha=0.35, solid_capstyle="round", zorder=2)
        ax.scatter([m], [yy], s=34, color=c, zorder=4, edgecolors=CARD, linewidths=0.8)
        ax.text(m * 1.14, yy, f"{fmt_lag(m)}  ·  {who}", va="center", fontsize=6.6, color=WHITE)
    ax.set_xscale("log"); ax.set_xlim(4, 9000); ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xticks([5, 15, 60, 240, 1440, 2880]); ax.set_xticklabels(["5 min", "15 min", "1 h", "4 h", "24 h", "48 h"], fontsize=6.6)
    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=7.2, color=WHITE); ax.grid(axis="x", color=GRID, lw=0.6); ax.grid(axis="y", visible=False)
    ax.axvline(60, color=MUTED, lw=0.6, ls=(0, (2, 2)))
    from matplotlib.lines import Line2D
    ax.legend([Line2D([], [], marker="o", ls="", color=BLUE), Line2D([], [], marker="o", ls="", color=RED)], ["setup, before the drain", "during the drain"],
              loc="lower right", fontsize=6.6, frameon=False, labelcolor=BODY)
    ax.set_xlabel("Time from the on-chain event to the first public post describing it (log scale)", fontsize=6.8)
    return save(fig, "g_detect_lag")

# ---------------------------------------------------------------- 4. freeze ladder
def ladder():
    fig, ax = plt.subplots(figsize=(7.4, 2.9))
    steps = [("10-29 20:24", 0.0, ""), ("10-29 21:05", 0.971, "Tether $971M (first report)"), ("10-29 21:18", 1.771, "+ Circle >$800M"),
             ("10-29 21:25", 2.367, "Tether raises to $1.567B"), ("10-29 22:22", 2.396, "+ WLFI $27M USD1 + ~$2M WLFI")]
    xs = [T(s) for s, _, _ in steps] + [T("10-30 01:00")]; ys = [v for _, v, _ in steps]
    ax.step(xs, ys + [ys[-1]], where="post", color=GREEN, lw=1.8, zorder=3)
    ax.fill_between(xs, ys + [ys[-1]], step="post", color=GREEN, alpha=0.10, zorder=2)
    OFFS = {"Tether $971M (first report)": (7, -11), "+ Circle >$800M": (7, -11), "Tether raises to $1.567B": (-4, 6), "+ WLFI $27M USD1 + ~$2M WLFI": (7, -11)}
    for (s, v, lab) in steps[1:]:
        ax.scatter([T(s)], [v], s=18, color=GREEN, zorder=4, edgecolors=CARD)
        o = OFFS[lab]; ax.annotate(lab, (T(s), v), xytext=o, textcoords="offset points", fontsize=6.4, color=WHITE, ha="right" if o[0] < 0 else "left")
    for s, v, lab in (("10-29 23:22", 2.54, "Binance: $2.54B verified frozen"), ("10-30 00:52", 3.0, "Binance: ~$3B verified frozen")):
        ax.scatter([T(s)], [v], s=30, marker="D", color=AMBER, zorder=5, edgecolors=CARD)
        ax.annotate(lab, (T(s), v), xytext=(0, 7), textcoords="offset points", fontsize=6.4, color=AMBER, ha="center")
    ax.set_xlim(T("10-29 20:15"), T("10-30 01:05")); ax.set_ylim(0, 3.45)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"${v:.1f}B")); ax.tick_params(labelsize=6.6)
    ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute=[0, 30])); ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.grid(axis="y", color=GRID, lw=0.6); ax.grid(axis="x", visible=False)
    return save(fig, "g_freeze_ladder")

# ---------------------------------------------------------------- 5. cover glow (smooth, dithered, no banding) + cover art strip
def cover_bg(w_in=8.5, h_in=11.0, dpi=200):
    W, H = int(w_in * dpi), int(h_in * dpi)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = np.array([11, 18, 30], np.float32)            # #0B121E
    glow = np.array([20, 184, 129], np.float32)          # brand green
    blue = np.array([110, 166, 248], np.float32)
    cx, cy = 0.80 * W, 0.56 * H; r = np.hypot(xx - cx, yy - cy) / (0.62 * H)
    g = np.clip(1 - r, 0, 1) ** 2.6 * 0.20                # soft, single falloff
    r2 = np.hypot(xx - 0.05 * W, yy - 0.02 * H) / (0.55 * H)
    b = np.clip(1 - r2, 0, 1) ** 3.0 * 0.07
    # faint rings that fade into the glow (modulated, never stepped)
    rings = (0.5 + 0.5 * np.cos(r * np.pi * 7.0)) * np.clip(1 - r, 0, 1) ** 1.6 * 0.022
    img = base + (glow - base) * (g + rings)[..., None] + (blue - base) * b[..., None]
    img += (np.random.default_rng(7).random((H, W, 1), dtype=np.float32) - 0.5) * 1.6   # dither kills 8-bit banding
    # vignette
    v = np.clip(1 - 0.18 * (np.hypot((xx - W / 2) / W, (yy - H / 2) / H) * 1.6) ** 2, 0.82, 1)
    img = np.clip(img * v[..., None], 0, 255).astype(np.uint8)
    p = os.path.join(OUT, "cover_bg.png"); Image.fromarray(img).save(p, optimize=True); return p

def cover_art():
    """Minimal transparent timeline for the cover: the 43 hours as lanes, setup dim, the night lit."""
    fig, ax = plt.subplots(figsize=(7.06, 2.2)); fig.patch.set_alpha(0); ax.set_facecolor((0, 0, 0, 0))
    L, R = T("10-28 06:00"), T("10-30 01:00"); ax.set_xlim(L, R + dt.timedelta(minutes=40)); ax.set_ylim(0.3, 4.9); ax.axis("off")
    rows = {"fund": 4, "prep": 3, "attack": 2, "response": 1}
    for k, y in rows.items(): ax.plot([L, R], [y, y], color="white", alpha=0.07, lw=0.6)
    for lane, s, e, lab in SETUP:
        y = rows[lane]
        if e: ax.plot([T(s), T(e)], [y, y], color=LANE[lane], lw=5, solid_capstyle="round")
        else: ax.scatter([T(s)], [y], s=14, color=LANE[lane], edgecolors="none")
    ax.plot(list(WINDOW), [2, 2], color=RED, lw=5, solid_capstyle="round")
    for s, e, lab in NIGHT["attack"]: ax.scatter([T(s)], [2], s=12, color="white", zorder=5, edgecolors="none")
    for s, e, lab in NIGHT["issuer"] + NIGHT["binance"]: ax.scatter([T(s)], [1], s=12, color=GREEN if (s, e, lab) in NIGHT["issuer"] else AMBER, edgecolors="none")
    for k, lab in (("fund", "FUNDING"), ("prep", "BUILD AND REHEARSE"), ("attack", "BINANCE 14"), ("response", "FREEZES AND RESPONSE")):
        ax.text(L, rows[k] + 0.28, lab, fontsize=5.6, color="white", alpha=0.55, fontweight=700)
    ax.text(T("10-28 06:00"), 0.42, "OCT 28, 06:00 UTC", fontsize=5.6, color="white", alpha=0.55, fontweight=600)
    ax.text(R, 0.42, "OCT 30, 01:00 UTC", fontsize=5.6, color="white", alpha=0.55, fontweight=600, ha="right")
    ax.text(T("10-29 20:24"), 4.55, "20:24  DRAIN", fontsize=6.0, color=RED, fontweight=700, ha="right")
    ax.axvline(T("10-29 20:24"), color=RED, lw=0.7, alpha=0.6, ymin=0.08, ymax=0.9)
    return save(fig, "g_cover_art", transparent=True)

# ---------------------------------------------------------------- 6. operator cascade + delegation window (v2 restyle of v1 charts, corrected to 3h 49m)
OPS = [("10-28 07:39", "Tornado 0.1 ETH", "fund"), ("10-28 08:53", "Tornado 0.1 ETH", "fund"), ("10-29 02:28:59", "sweeper v1 deployed", "prep"), ("10-29 08:23", "Tornado 0.1 ETH", "fund"),
       ("10-29 13:51:35", "rehearsal 1: delegate 2 test wallets", "rehearse"), ("10-29 14:19:59", "rehearsal 1: sweep", "rehearse"), ("10-29 15:59:11", "sweeper v2 deployed", "prep"),
       ("10-29 16:20:47", "rehearsal 2: delegate test wallet 3", "rehearse"), ("10-29 16:30:11", "rehearsal 2: sweep, withdraw 16:47", "rehearse"), ("10-29 18:20:47", "gas: 1.082 ETH", "fund"),
       ("10-29 20:20:59", "delegation: 50 authorizations", "attack"), ("10-29 20:24:23", "sweep: 167,464 ETH + 63 tokens", "attack"), ("10-29 20:41:23", "780M USDC via Hot Wallet 34", "attack"),
       ("10-29 20:59:47", "43M USDC", "attack"), ("10-29 21:04", "re-sweep 3.9M USDT", "attack"), ("10-29 21:44", "re-sweep 200.4M USDT", "attack"), ("10-29 22:39", "long-tail basket", "attack"),
       ("10-30 00:10:35", "Binance 14 revokes", "revoke")]
def operator():
    col = {"fund": SLATE, "prep": BLUE, "rehearse": AMBER, "attack": RED, "revoke": GREEN}; name = {"fund": "funding", "prep": "contracts", "rehearse": "rehearsals", "attack": "attack", "revoke": "revocation"}
    fig, ax = plt.subplots(figsize=(7.4, 4.3)); n = len(OPS)
    for i, (ts, lab, kind) in enumerate(OPS):
        y = n - i; t = T(ts)
        ax.plot([T("10-28 06:00"), t], [y, y], color=GRID, lw=0.6, zorder=1)
        ax.scatter([t], [y], s=26, color=col[kind], zorder=3, edgecolors=CARD, linewidths=0.7)
        ax.text(t + dt.timedelta(minutes=40), y, f"{ts[6:11]}  {lab}", va="center", fontsize=6.5, color=WHITE, zorder=4, bbox=dict(boxstyle="square,pad=0.15", fc=CARD, ec="none"))
    ax.axvline(T("10-29 20:24:23"), color=RED, lw=0.7, ls=(0, (2, 2)), alpha=0.8, zorder=0)
    ax.set_xlim(T("10-28 06:00"), T("10-30 08:30")); ax.set_ylim(0.3, n + 0.8); ax.set_yticks([]); ax.grid(axis="y", visible=False); ax.grid(axis="x", color=GRID, lw=0.6)
    ax.xaxis.set_major_locator(matplotlib.ticker.FixedLocator([mdates.date2num(T(x)) for x in ("10-28 06:00", "10-28 18:00", "10-29 06:00", "10-29 18:00", "10-30 06:00")]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d %H:%M")); ax.tick_params(axis="x", labelsize=6.4)
    from matplotlib.lines import Line2D
    ax.legend([Line2D([], [], marker="o", ls="", color=c) for c in col.values()], [name[k] for k in col], fontsize=6.6, ncol=5, loc="lower left", frameon=False, labelcolor=BODY, bbox_to_anchor=(0, 1.0))
    return save(fig, "g_operator_v2")
def hijack():
    fig, ax = plt.subplots(figsize=(7.4, 2.9))
    ev = [("10-29 20:24:23", "20:24 sweep\n1.615B USDT + 167,464 ETH\n+ 62 more tokens", 1985, RED), ("10-29 20:41:23", "20:41\n780M USDC", 780, RED), ("10-29 20:59:47", "20:59\n43M USDC", 43, RED),
          ("10-29 21:04", "21:04\n3.9M USDT", 3.9, RED), ("10-29 21:44", "21:44\n200.4M USDT + others", 200.4, RED), ("10-29 22:39", "22:39\nbasket, $7.5M+", 7.5, RED)]
    ax.axvspan(*WINDOW, color=RED, alpha=0.06, lw=0)
    side = {"10-29 20:41:23": "right", "10-29 21:04": "right"}
    for ts, lab, v, c in ev:
        ax.bar([T(ts)], [v], width=0.0030, color=c, zorder=3, bottom=1)
        if ts == "10-29 20:24:23": ax.text(T(ts) + dt.timedelta(minutes=4), v * 2.3, lab, ha="left", va="center", fontsize=6.1, color=WHITE, linespacing=1.15)
        elif ts == "10-29 21:04": ax.text(T(ts) + dt.timedelta(minutes=4), v, lab, ha="left", va="center", fontsize=6.1, color=WHITE, linespacing=1.15)
        elif side.get(ts) == "right": ax.text(T(ts) + dt.timedelta(minutes=4), v, lab.replace("\n", "  "), ha="left", va="center", fontsize=6.1, color=WHITE)
        else: ax.text(T(ts), v * 1.35, lab, ha="center", va="bottom", fontsize=6.1, color=WHITE, linespacing=1.15)
    for ts, lab, c in (("10-29 20:20:59", "20:21 delegation", AMBER), ("10-30 00:10:35", "00:10 revocation", GREEN)):
        ax.axvline(T(ts), color=c, lw=0.9, alpha=0.9); ax.text(T(ts) + dt.timedelta(minutes=3) if "revoc" in lab else T(ts) + dt.timedelta(minutes=3), 25000, lab, fontsize=6.2, color=c, ha="left", va="center")
    ax.text(T("10-29 23:15"), 900, "attacker code live: 3h 49m\n533 incoming transfers arrive", ha="center", fontsize=6.6, color=RED, linespacing=1.3)
    ax.set_yscale("log"); ax.set_ylim(1, 60000); ax.set_xlim(T("10-29 20:00"), T("10-30 00:40"))
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"${v / 1000:g}B" if v >= 1000 else f"${v:g}M"))
    ax.set_yticks([1, 10, 100, 1000]); ax.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute=[0, 30])); ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M")); ax.tick_params(labelsize=6.4)
    ax.grid(axis="y", color=GRID, lw=0.6); ax.grid(axis="x", visible=False)
    return save(fig, "g_hijack_v2")

if __name__ == "__main__":
    idx_p = os.path.join(HERE, "charts_index.json"); idx = json.load(open(idx_p))
    for fn in (master, night, lag, ladder, cover_art, operator, hijack):
        p = fn(); idx[os.path.basename(p)[:-4]] = p; print("chart", p)
    print("bg", cover_bg())
    json.dump(idx, open(idx_p, "w"), indent=1)
