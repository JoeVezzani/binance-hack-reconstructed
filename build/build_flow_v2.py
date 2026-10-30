#!/usr/bin/env python3
"""v2 money charts from the live re-verification (onchain/reverify_20261030T032016Z/positions.json). Additive: writes g_flow_v2 / g_positions_v2."""
import os, json
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.ticker as mt, matplotlib.patches as mpatches

import matplotlib.text as _mtext
_text_init = _mtext.Text.__init__
def _text_init_nocalt(self, *a, **k):  # Plus Jakarta's contextual alternates turn "0x" into "0×"; keep it literal
    _text_init(self, *a, **k); self.set_fontfeatures(["-calt"])
_mtext.Text.__init__ = _text_init_nocalt
from matplotlib.path import Path as MPath
from matplotlib import font_manager as fm
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
for f in ("PlusJakartaSans-400.ttf", "PlusJakartaSans-600.ttf", "PlusJakartaSans-700.ttf"): fm.fontManager.addfont(os.path.join(HERE, "fonts", f))
CARD, WHITE, BODY, MUTED, GRID = "#0D1522", "#FFFFFF", "#A9AEC0", "#69718C", "#1A2433"
GREEN, BLUE, AMBER, RED, VIOLET, PINK, CYAN, SLATE = "#14B881", "#6EA6F8", "#F2A93B", "#FF7A7A", "#B794F6", "#E88BB5", "#22D3EE", "#7C8599"
plt.rcParams.update({"text.parse_math": False, "font.family": "Plus Jakarta Sans", "font.size": 8, "text.color": BODY, "axes.facecolor": CARD, "figure.facecolor": CARD, "savefig.facecolor": CARD,
    "axes.edgecolor": GRID, "xtick.color": MUTED, "ytick.color": MUTED, "xtick.major.size": 0, "ytick.major.size": 0, "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False, "axes.spines.bottom": False})
FS = json.load(open(os.path.join(ROOT, "onchain", "reverify_20261030T032016Z", "positions.json")))
# Reclassify the Aave position: aUSDT collateral net of WETH debt is not frozen (a reserve freeze still allows withdrawals).
_aave = [f for f in FS["frozen"] if "Aave" in f["asset"]]
for f in _aave:
    FS["frozen"].remove(f); FS["held"].append({**f, "usd": 16.3, "asset": "aUSDT (Aave), net of debt", "status": "Collateral net of WETH debt; withdrawable within health-factor limits"})
_amt = sum(f["usd"] for f in _aave)  # frozen side loses the recorded 16.2
_add = 16.3 * len(_aave)               # 60,002,066.5 aUSDT - 19,762.70 WETH x $2,209.99 = $16.33M
FS["totals"]["frozen_or_recovered_usd_m"] = round(FS["totals"]["frozen_or_recovered_usd_m"] - _amt, 1)
FS["totals"]["held_unfrozen_usd_m"] = round(FS["totals"]["held_unfrozen_usd_m"] + _add, 1)
FS["chart_flows_usd_m"]["Ethereum|Frozen or recovered"] = round(FS["chart_flows_usd_m"]["Ethereum|Frozen or recovered"] - _amt, 1)
FS["chart_flows_usd_m"]["Ethereum|Unfrozen, traced"] = round(FS["chart_flows_usd_m"]["Ethereum|Unfrozen, traced"] + _add, 1)
FS["chart_sources_usd_m"]["Ethereum"] = round(FS["chart_sources_usd_m"]["Ethereum"] - _amt + _add, 1)
def save(fig, name):
    p = os.path.join(HERE, "charts", name + ".png"); fig.savefig(p, dpi=260, bbox_inches="tight", pad_inches=0.1); plt.close(fig); print(p)
def money(v): return f"${v / 1000:.2f}B" if v >= 1000 else f"${v:,.0f}M"
COL = {"Ethereum": BLUE, "Bitcoin": AMBER, "Tron": PINK, "XRP Ledger": VIOLET, "Solana": SLATE, "Arbitrum": CYAN}
def band(ax, x0, y0, h0, x1, y1, h1, color, alpha=0.42):
    xm = (x0 + x1) / 2
    v = [(x0, y0), (xm, y0), (xm, y1), (x1, y1), (x1, y1 + h1), (xm, y1 + h1), (xm, y0 + h0), (x0, y0 + h0), (x0, y0)]
    c = [MPath.MOVETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4, MPath.LINETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4, MPath.CLOSEPOLY]
    ax.add_patch(mpatches.PathPatch(MPath(v, c), facecolor=color, edgecolor="none", alpha=alpha, zorder=2))
fig, ax = plt.subplots(figsize=(7.4, 4.4)); ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
SRC = sorted(FS["chart_sources_usd_m"].items(), key=lambda kv: -kv[1]); DST = [("Frozen or recovered", FS["totals"]["frozen_or_recovered_usd_m"], GREEN), ("Unfrozen, traced", FS["totals"]["held_unfrozen_usd_m"], RED)]
FL = {tuple(k.split("|")): v for k, v in FS["chart_flows_usd_m"].items()}
tot = sum(v for _, v in SRC); gap = 0.16; scale = (9.2 - gap * (len(SRC) - 1)) / tot; y = 9.6; spos = {}; labs = []
for name, v in SRC:
    h = v * scale; y -= h; spos[name] = (y, h); ax.add_patch(mpatches.Rectangle((2.0, y), 0.36, h, color=COL[name], zorder=3, lw=0)); labs.append([y + h / 2, f"{name}   {money(v)}"]); y -= gap
for l in labs: l.append(l[0])  # remember the node center
labs.sort(key=lambda l: l[0])
for _ in range(60):  # relax overlapping labels symmetrically around their nodes
    moved = False
    for a_, b_ in zip(labs, labs[1:]):
        if b_[0] - a_[0] < 0.42:
            d = (0.42 - (b_[0] - a_[0])) / 2; a_[0] -= d; b_[0] += d; moved = True
    if not moved: break
for ly, t, cy in labs:
    ax.text(1.80, ly, t, ha="right", va="center", fontsize=7.4, color=WHITE)
    if abs(ly - cy) > 0.04: ax.plot([1.83, 1.98], [ly, cy], color=MUTED, lw=0.6)
dscale = (9.2 - 0.5) / sum(v for _, v, _ in DST); y = 9.6; dpos = {}
for name, v, c in DST:
    h = v * dscale; y -= h; dpos[name] = (y, h); ax.add_patch(mpatches.Rectangle((7.7, y), 0.36, h, color=c, zorder=3, lw=0))
    ax.text(8.2, y + h / 2 + 0.25, money(v), ha="left", va="center", fontsize=13, color=WHITE, fontweight=700); ax.text(8.2, y + h / 2 - 0.35, name, ha="left", va="center", fontsize=7.4, color=BODY); y -= 0.5
so = {k: a + b for k, (a, b) in spos.items()}; do = {k: a + b for k, (a, b) in dpos.items()}
for name, _ in SRC:
    for d in ("Frozen or recovered", "Unfrozen, traced"):
        v = FL.get((name, d))
        if not v: continue
        h0, h1 = v * scale, v * dscale; so[name] -= h0; do[d] -= h1; band(ax, 2.36, so[name], h0, 7.7, do[d], h1, COL[name])
save(fig, "g_flow_v2")
import re as _re
_SHORT = {}
for _row in json.load(open(os.path.join(ROOT, "chapters_v2", "flow.json")))["table"]["rows"]:
    for _m in _re.findall(r"0x[0-9a-fA-F]{4}…[0-9a-fA-F]{4}", _row[0]): _SHORT[_m[:6].lower()] = _m
def _addr(w):
    w = w.split(" (")[0]
    return _SHORT.get(w[:6].lower(), w) if w.startswith("0x") else w
def lab(x): return f"{x['asset']}  ·  {_addr(x['where'])[:24]}"
rows = [(lab(h), h["usd"], RED) for h in FS["held"]] + [(lab(f), f["usd"], GREEN) for f in FS["frozen"]]; rows.sort(key=lambda r: -r[1])
fig, ax = plt.subplots(figsize=(7.4, 0.24 * len(rows) + 0.6)); y = list(range(len(rows)))[::-1]
ax.barh(y, [r[1] for r in rows], color=[r[2] for r in rows], height=0.6, zorder=3)
ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], color=WHITE, fontsize=7.0, fontfamily="Plus Jakarta Sans"); ax.grid(axis="x", color=GRID, lw=0.6); ax.grid(axis="y", visible=False)
for yy, r in zip(y, rows): ax.text(r[1] + 14, yy, money(r[1]), va="center", fontsize=6.6, color=WHITE)
ax.set_xlim(0, max(r[1] for r in rows) * 1.18); ax.xaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: "$0" if v == 0 else (f"${v / 1000:.1f}B" if v >= 1000 else f"${v:.0f}M"))); ax.tick_params(labelsize=6.8)
from matplotlib.lines import Line2D
ax.legend([Line2D([], [], marker="s", ls="", color=RED), Line2D([], [], marker="s", ls="", color=GREEN)], ["unfrozen, traced", "frozen or recovered"], fontsize=6.8, loc="lower right", frameon=False, labelcolor=BODY)
save(fig, "g_positions_v2")
