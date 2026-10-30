#!/usr/bin/env python3
"""Render every chart for the Binance hack report from analysis.json into build/charts/. Writes charts_index.json."""
import json, os, sys, datetime, math
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import charts as C
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mt
from adjustText import adjust_text
UTC = datetime.timezone.utc
A = json.load(open(os.path.join(ROOT, "analysis.json")))
BH = A["binance_hourly"]; POST = BH["post"]; FULL = [h for h in POST if not h["partial"]]; BASE = BH["baseline"]
T0 = 1793304000; EV = 1793305440
out = {}
def ts(t): return datetime.datetime.fromtimestamp(t, UTC)
def save(fig, name):
    out[name] = C._save(fig, name); return out[name]
LAB = [h["utc"][-5:] for h in POST]
PINK, PURPLE, GREY = "#F472B6", "#C084FC", "#94A3B8"
def nominor(ax, which="both"):
    if which in ("both", "x"): ax.xaxis.set_minor_locator(mt.NullLocator())
    if which in ("both", "y"): ax.yaxis.set_minor_locator(mt.NullLocator())
    ax.tick_params(which="minor", length=0)
def sgn(v):  # signed integer label with a true minus sign; zero has no sign
    v = int(round(v)); return "0" if v == 0 else (f"+{v}" if v > 0 else f"\u2212{abs(v)}")
LAST_FULL = 1793318400
def hfmt(x, _=None): return "0" if x == 0 else (f"{x/1e6:g}M" if x >= 1e6 else (f"{x/1e3:g}K" if x >= 1e3 else f"{x:g}"))  # 00:00 UTC Oct 30, the last full hour at the data cut

# 1. 7-day hourly engagements with event marker
fig, ax = plt.subplots(figsize=(6.8, 2.6))
WEEK = [r for r in BH["pre_series"] if r[0] <= LAST_FULL]  # drop the partial 01:00 bucket
t = [ts(r[0]) for r in WEEK]; v = [r[1] for r in WEEK]
ax.fill_between(t, v, color=C.GREEN, alpha=0.18); ax.plot(t, v, color=C.GREEN, lw=1.5)
ax.set_xlim(t[0], t[-1]); ax.set_ylim(0, max(v) * 1.08)
ax.axvline(ts(EV), color=C.AMBER, lw=0.9, ls=(0, (3, 3))); ax.text(ts(EV - 1800), max(v) * 0.97, "20:24 UTC sweep", color=C.AMBER, fontsize=7, va="top", ha="right")
ax.axhline(BASE["interactions"], color=C.MUTED, lw=0.7, ls=(0, (2, 3))); ax.text(t[0] + datetime.timedelta(hours=3), max(v) * 0.16, f"7-day baseline {C.human(BASE['interactions'])}/h", color=C.MUTED, fontsize=6.8)
ax.annotate("", (t[0] + datetime.timedelta(hours=12), BASE["interactions"]), xytext=(t[0] + datetime.timedelta(hours=12), max(v) * 0.15), arrowprops=dict(arrowstyle="-", color=C.MUTED, lw=0.5))
ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda x, _: f"{x/1e6:g}M" if x else "0")); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d")); ax.tick_params(labelsize=7.5)
ax.set_ylabel("Engagements per hour", fontsize=7.5); ax.set_title("Binance topic, engagements per hour, Oct 23 to Oct 30 (UTC)")
save(fig, "g_week_hourly")

# 2. event-hour multiples: engagements vs new posts vs first-time posters
fig, ax = plt.subplots(figsize=(6.8, 2.7))
x = range(len(FULL)); w = 0.26
xe = [h["x_base"] for h in FULL]; xp = [h["x_posts"] for h in FULL]; xc = [h["contributors_created"] / BASE["contributors_created"] for h in FULL]
for i, (vals, col, lab) in enumerate(((xe, C.GREEN, "Engagements"), (xp, C.BLUE, "New posts"), (xc, C.AMBER, "First-time posters"))):
    ax.bar([xx + (i - 1) * w for xx in x], vals, width=w, color=col, label=lab, zorder=3)
    for xx, vv in zip(x, vals): ax.text(xx + (i - 1) * w, vv + 0.4, f"{vv:.1f}x", ha="center", fontsize=6.0, color=C.WHITE)
ax.set_xticks(list(x)); ax.set_xticklabels([h["utc"][-5:] + " UTC" for h in FULL], fontsize=7.5, color=C.WHITE); ax.grid(axis="x", visible=False)
ax.set_ylim(0, max(xe + xp + xc) * 1.12); ax.set_ylabel("Multiple of 7-day hourly baseline", fontsize=7.5); ax.legend(ncol=3, loc="upper left", fontsize=7)
ax.set_title("Each event hour against its own baseline (20:00 bucket holds only 36 minutes of event)")
save(fig, "g_event_multiples")

# 3. minute cumulative (sampled posts)
mc = A["minute_cum_interactions"]
fig, ax = plt.subplots(figsize=(6.8, 2.6))
ax.plot(range(len(mc)), mc, color=C.GREEN, lw=1.8); ax.fill_between(range(len(mc)), mc, color=C.GREEN, alpha=0.15)
marks = [(8, "@spreekaway +8", (12, 0), "left"), (41, "Tether freeze\nheadlines +41", (14, -7), "left"), (51, "CZ and @binance +51", (-10, 14), "right"), (94, "@KobeissiLetter\n$5.7B +94", (10, -26), "left"), (129, "@elonmusk +129", (10, -18), "left"), (268, "Binance: ~$3B\nfrozen +268", (-10, -30), "right")]
for m, lab, off, ha in marks:
    if m < len(mc):
        ax.plot([m], [mc[m]], "o", color=C.WHITE, ms=3.5, zorder=4)
        ax.annotate(lab, (m, mc[m]), xytext=off, textcoords="offset points", fontsize=6.3, color=C.BODY, ha=ha, va="center", arrowprops=dict(arrowstyle="-", color=C.MUTED, lw=0.5, shrinkA=0, shrinkB=2.5))
ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda x, _: C.human(x))); ax.set_xlabel("Minutes after 20:24 UTC", fontsize=7.5); ax.set_ylabel("Cumulative engagements, sampled posts", fontsize=7.5); ax.tick_params(labelsize=7.5)
ax.set_title("How fast the sampled posts accumulated engagement (686 top posts, final engagement counts)")
save(fig, "g_minute_cum")

# 4. sentiment 7-day
fig, ax = plt.subplots(figsize=(6.8, 2.2))
s = [r[2] for r in WEEK]
ax.plot(t, s, color=C.BLUE, lw=1.5); ax.axvline(ts(EV), color=C.AMBER, lw=0.9, ls=(0, (3, 3))); ax.set_ylim(40, 100)
ax.axhline(BASE["sentiment"], color=C.MUTED, lw=0.7, ls=(0, (2, 3))); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d")); ax.tick_params(labelsize=7.5)
ax.set_xlim(t[0], t[-1]); ax.annotate(f"prior-week avg {BASE['sentiment']:.0f}", (t[0] + datetime.timedelta(hours=80), BASE["sentiment"]), xytext=(t[0] + datetime.timedelta(hours=80), 70), ha="center", va="top", color=C.MUTED, fontsize=6.8, arrowprops=dict(arrowstyle="-", color=C.MUTED, lw=0.5))
ax.text(ts(EV - 1800), 97, "20:24 sweep", color=C.AMBER, fontsize=6.8, ha="right", va="top")
ax.set_ylabel("Sentiment (0-100)", fontsize=7.5); ax.set_title("Binance sentiment per hour: 80 average for the week, 53 at 21:00 UTC")
save(fig, "g_sent_week")

# 5. sentiment event hours, several topics
fig, ax = plt.subplots(figsize=(6.8, 2.6))
want = ["binance", "tether", "usdc", "bybit", "bnb", "bitcoin", "ethereum"]
cmap = {"binance": C.GREEN, "tether": C.AMBER, "usdc": C.BLUE, "bybit": C.RED, "bnb": PURPLE, "bitcoin": GREY, "ethereum": PINK}
cont = {c["topic"]: c for c in A["contagion"]}
for tname in want:
    c = cont.get(tname)
    if not c: continue
    ax.plot(["pre"] + [h["utc"] for h in c["hours"]], [c["sent_pre"]] + [h["sentiment"] for h in c["hours"]], marker="o", ms=3, lw=1.5, color=cmap[tname], label=c["display"])
ax.set_ylim(30, 95); ax.legend(ncol=4, fontsize=6.8, loc="lower left"); ax.tick_params(labelsize=7.5); ax.set_ylabel("Sentiment (0-100)", fontsize=7.5)
ax.set_title("Sentiment by hour (UTC) for Binance and the topics it dragged")
save(fig, "g_sent_event")

# 6. sentiment by network (24h)
ns = A["network_24h"]["sentiment"]; order = [("tweet", "X"), ("tiktok-video", "TikTok"), ("youtube-video", "YouTube"), ("instagram-post", "Instagram"), ("reddit-post", "Reddit"), ("news", "News")]
C.hbar("g_sent_network", [n for _, n in order], [ns[k] for k, _ in order], w=3.3, h=2.0, color=C.BLUE, fmt=lambda v: f"{v:.0f}", ref=None, xlabel="Sentiment, last 24h (0-100)")
out["g_sent_network"] = os.path.join(C.OUT, "g_sent_network.png")

# 7. newcomers: first-time posters per hour + share of active
fig, ax = plt.subplots(figsize=(6.8, 2.6))
ax.bar(LAB[:-1], [h["contributors_created"] for h in FULL], color=C.AMBER, width=0.6, zorder=3, label="First-time posters (count)")
ax.axhline(BASE["contributors_created"], color=C.MUTED, lw=0.8, ls=(0, (3, 3))); ax.set_xlim(-0.5, len(FULL) - 0.5 + 0.75); ax.text(len(FULL) - 0.5 + 0.72, BASE["contributors_created"], f"baseline\n{BASE['contributors_created']:.0f}/h", color=C.MUTED, fontsize=6.5, ha="right", va="bottom", linespacing=1.1)
ax2 = ax.twinx(); ax2.plot(LAB[:-1], [h["new_creator_share_of_active"] * 100 for h in FULL], color=C.WHITE, marker="o", ms=3.5, lw=1.4, label="Share of active creators posting for the first time")
ax2.set_ylim(0, 60); ax2.grid(False); ax2.set_ylabel("Share of active creators (%)", fontsize=7.5); ax2.tick_params(labelsize=7.5); ax2.spines["right"].set_visible(False)
for xlab, h in zip(LAB[:-1], FULL): ax2.text(xlab, h["new_creator_share_of_active"] * 100 + 2.5, f"{h['new_creator_share_of_active']*100:.0f}%", ha="center", fontsize=7, color=C.WHITE)
ax.yaxis.set_major_formatter(mt.FuncFormatter(hfmt)); ax.set_ylabel("First-time posters per hour", fontsize=7.5); ax.tick_params(labelsize=7.5); ax.grid(axis="x", visible=False)
ax.set_title(f"First-time posters per hour and their share of all active creators (baseline share {BASE['new_creator_share_of_active']*100:.0f}%)")
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels(); ax.legend(h1 + h2, l1 + l2, fontsize=6.8, loc="upper right")
save(fig, "g_newcomers")

# 8. spam share
fig, ax = plt.subplots(figsize=(3.3, 2.0))
ax.bar(["base"] + LAB[:-1], [BASE["spam_share"] * 100] + [h["spam_share"] * 100 for h in FULL], color=[C.MUTED] + [C.GREEN] * len(FULL), width=0.6, zorder=3)
for i, v in enumerate([BASE["spam_share"] * 100] + [h["spam_share"] * 100 for h in FULL]): ax.text(i, v + 0.3, f"{v:.1f}%", ha="center", fontsize=6.8, color=C.WHITE)
ax.set_ylabel("Spam share of active posts (%)", fontsize=7); ax.tick_params(labelsize=7); ax.grid(axis="x", visible=False); ax.set_title("Spam share fell as volume rose", fontsize=9)
save(fig, "g_spam")

# 9. contagion peak multiples (flag pre-elevated)
PRE = {"hyperliquid", "mstr", "kraken"}
cc = [c for c in A["contagion"] if c["topic"] not in ("coin",)]
labels = [c["display"] + (" *" if c["topic"] in PRE else "") for c in cc]; vals = [c["peak_x"] for c in cc]
fig, ax = plt.subplots(figsize=(6.8, 4.6))
y = list(range(len(labels)))[::-1]
cols = [C.GREEN if c["topic"] == "binance" else (C.AMBER if c["topic"] in PRE else C.BLUE) for c in cc]
ax.barh(y, vals, color=cols, height=0.62, zorder=3); ax.set_yticks(y); ax.set_yticklabels(labels, color=C.WHITE, fontsize=8); ax.grid(axis="y", visible=False)
for yy, v, c in zip(y, vals, cc): ax.text(v + 0.8, yy, f"{v:.1f}x  (peak {c['peak_utc']}, {C.human(c['peak_int_h'])}/h vs {C.human(c['base_int_h'])}/h)", va="center", fontsize=6.6, color=C.WHITE)
ax.set_xlim(0, max(vals) * 1.55); ax.set_xlabel("Peak hourly engagements, 20:00 to 00:00 UTC, as a multiple of each topic's own 7-day baseline", fontsize=7.5); ax.tick_params(labelsize=7.5)
ax.set_title("Attention spillover: which topics spiked with Binance (* already elevated before 20:24 UTC)")
save(fig, "g_contagion")

# 10. contagion lines
fig, ax = plt.subplots(figsize=(6.8, 2.7))
for tname in ["binance", "tether", "usdc", "ethereum", "bnb", "bitcoin", "bybit"]:
    c = cont.get(tname)
    if c: ax.plot([h["utc"] for h in c["hours"]], [h["x"] for h in c["hours"]], marker="o", ms=3, lw=1.6, color=cmap[tname], label=c["display"])
ax.set_yscale("log"); ax.set_ylim(0.8, 130); ax.yaxis.set_major_locator(mt.FixedLocator([1, 3, 10, 30, 100])); nominor(ax, "y"); ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda x, _: f"{x:g}x")); ax.set_ylabel("Multiple of own baseline (log)", fontsize=7.5); ax.legend(ncol=7, fontsize=6.8, loc="upper center", bbox_to_anchor=(0.5, -0.1), handlelength=1.2, columnspacing=1.0); ax.tick_params(labelsize=7.5)
ax.set_title("Hour by hour (UTC): Tether outran Binance on a relative basis")
save(fig, "g_contagion_lines")

# 11. sentiment delta by topic
# deltas from the same rounded integers the table shows (e.g. Bybit 75 to 54 = -21)
sd = sorted([(c["display"], round(c["sent_post"]) - round(c["sent_pre"])) for c in cc], key=lambda r: (r[1], r[0]))
fig, ax = plt.subplots(figsize=(3.3, 4.2)); y = list(range(len(sd)))[::-1]
dv = [d for _, d in sd]
ax.barh(y, dv, color=[C.GREEN if d > 0 else (C.RED if d < 0 else C.MUTED) for d in dv], height=0.62, zorder=3)
ax.axvline(0, color=C.MUTED, lw=0.8, zorder=4)
ax.set_yticks(y); ax.set_yticklabels([n for n, _ in sd], color=C.WHITE, fontsize=8); ax.grid(axis="y", visible=False)
for yy, d in zip(y, dv):
    ax.text(d + (0.6 if d >= 0 else -0.6), yy, sgn(d), va="center", ha="left" if d >= 0 else "right", fontsize=7.2, fontweight=600, color=C.GREEN if d > 0 else (C.RED if d < 0 else C.BODY), zorder=5)
ax.set_xlim(min(dv) - 6, max(dv) + 5); ax.xaxis.set_major_formatter(mt.FuncFormatter(lambda x, _: sgn(x))); ax.tick_params(labelsize=7.5)
ax.set_xlabel("Sentiment change, event hours vs 7-day baseline", fontsize=7.5)
save(fig, "g_sent_delta")

# 12. network share (engagements and posts)
n24 = A["network_24h"]
rows = [("Engagements (114.2M)", n24["interactions"]), ("Posts (53.2K)", n24["posts"])]
out["g_network_share"] = C.network_stack("g_network_share", rows, w=6.8, h=1.5)

# 13. network timing (sampled)
nt = A["network_timing"]; ordn = [("tweet", "X"), ("youtube-video", "YouTube"), ("tiktok-video", "TikTok"), ("reddit-post", "Reddit")]
fig, ax = plt.subplots(figsize=(6.8, 2.2))
for i, (k, lab) in enumerate(ordn):
    v = nt[k]; yy = len(ordn) - i
    ax.plot([v["first_min_after"], v["median_min_after"]], [yy, yy], color=C.GRID, lw=3, zorder=2)
    ax.plot([v["first_min_after"]], [yy], "o", color=C.AMBER, ms=7, zorder=4); ax.plot([v["p10_min"]], [yy], "o", color=C.BLUE, ms=6, zorder=4); ax.plot([v["median_min_after"]], [yy], "o", color=C.GREEN, ms=7, zorder=4)
    ax.text(v["median_min_after"] + 4, yy, f"n={v['n']}", va="center", fontsize=7, color=C.MUTED)
ax.set_yticks(range(1, len(ordn) + 1)); ax.set_yticklabels([l for _, l in ordn][::-1], color=C.WHITE, fontsize=8.5); ax.grid(axis="y", visible=False)
ax.axvline(0, color=C.MUTED, lw=0.8, ls=(0, (3, 3))); ax.set_xlabel("Minutes after 20:24 UTC (first exploit transaction)", fontsize=7.5); ax.tick_params(labelsize=7.5)
ax.scatter([], [], color=C.AMBER, label="first sampled post"); ax.scatter([], [], color=C.BLUE, label="10th percentile"); ax.scatter([], [], color=C.GREEN, label="median"); ax.legend(ncol=3, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.28)); ax.set_ylim(0.4, len(ordn) + 0.6)
ax.set_title("When each network's sampled posts appeared (news and Instagram had no sampled posts in the window)")
save(fig, "g_network_timing")

# 14. sampled posts per hour by type
tb = A["types_by_hour"]; hrs = ["20:00", "21:00", "22:00", "23:00", "00:00"]
fig, ax = plt.subplots(figsize=(3.3, 2.2)); bottom = [0] * len(hrs)
for k, (lab, col) in C.NET.items():
    vals = [tb.get(h, {}).get(k, 0) for h in hrs]
    if sum(vals) == 0: continue
    ax.bar(hrs, vals, bottom=bottom, color=col, width=0.6, label=lab, zorder=3); bottom = [a + b for a, b in zip(bottom, vals)]
ax.legend(fontsize=6.5, ncol=2); ax.tick_params(labelsize=7); ax.grid(axis="x", visible=False); ax.set_title("Sampled posts per hour by network", fontsize=9)
save(fig, "g_types_hour")

# 15. themes by engagements
th = A["themes"]; tk = sorted(th.keys(), key=lambda k: -th[k]["interactions"])
fig, ax = plt.subplots(figsize=(6.8, 3.4)); y = list(range(len(tk)))[::-1]
ax.barh(y, [th[k]["interactions"] for k in tk], color=C.GREEN, height=0.62, zorder=3)
ax.set_yticks(y); ax.set_yticklabels(tk, color=C.WHITE, fontsize=8); ax.grid(axis="y", visible=False)
FIRST_FIX = {k: '20:41' for k in th if 'largest' in k.lower()}  # 20:30 match was an earnings post, not this event
for yy, k in zip(y, tk): ax.text(th[k]["interactions"] + 4e5, yy, f"{C.human(th[k]['interactions'])}   ({th[k]['posts']} posts, first {FIRST_FIX.get(k, th[k]['first_utc'][-5:])} UTC)", va="center", fontsize=6.8, color=C.WHITE)
ax.set_xlim(0, max(th[k]["interactions"] for k in tk) * 1.5); ax.xaxis.set_major_formatter(mt.FuncFormatter(lambda x, _: C.human(x))); ax.tick_params(labelsize=7.5)
ax.set_xlabel("Engagements on sampled posts matching the theme (a post can match several)", fontsize=7.5); ax.set_title("Which story each engagement went to")
save(fig, "g_themes")

# 16. themes by hour (stacked, counts)
fig, ax = plt.subplots(figsize=(6.8, 2.6)); bottom = [0] * len(hrs); pal = C.SERIES + [PINK, GREY, "#F59E0B", "#22D3EE"]
for i, k in enumerate(tk):
    vals = [th[k]["by_hour"].get(h, 0) for h in hrs]
    ax.bar(hrs, vals, bottom=bottom, color=pal[i % len(pal)], width=0.62, label=k, zorder=3); bottom = [a + b for a, b in zip(bottom, vals)]
ax.legend(fontsize=6.4, ncol=4, loc="lower center", bbox_to_anchor=(0.5, 1.0), handlelength=1.0, columnspacing=1.2); ax.tick_params(labelsize=7.5); ax.grid(axis="x", visible=False); ax.set_ylabel("Sampled posts", fontsize=7.5); ax.set_title("Theme mentions per hour in the sampled posts (UTC)")
save(fig, "g_themes_hour")

# 17. keyword dumbbells
kw = A["keywords"]; pick = [("binance_hack", "binance hack"), ("SAFU", "SAFU"), ("hot_wallet", "hot wallet"), ("not_your_keys", "not your keys"), ("largest_hack", "largest hack"), ("crypto_hack", "crypto hack"), ("bank_run", "bank run"), ("bybit_hack", "bybit hack"), ("tether_freeze", "tether freeze"), ("binance_withdrawals", "binance withdrawals"), ("EIP7702", "EIP-7702")]
fig, ax = plt.subplots(figsize=(6.8, 3.4)); y = list(range(len(pick)))[::-1]
for yy, (k, lab) in zip(y, pick):
    a = kw[k]["posts_prev"] or 1; b = kw[k]["posts_24h"] or 0
    ax.plot([a, b], [yy, yy], color=C.GRID, lw=3, zorder=2); ax.plot([a], [yy], "o", color=C.MUTED, ms=6, zorder=3); ax.plot([b], [yy], "o", color=C.GREEN, ms=7, zorder=4)
    ax.text(b * 1.25, yy, f"{a:,} to {b:,}  ({b / a:.1f}x)" if a > 1 and b / a < 10 else f"{a:,} to {b:,}  ({b / a:.0f}x)" if a > 1 else f"{a} to {b:,}", va="center", fontsize=6.9, color=C.WHITE)
ax.set_xscale("log"); nominor(ax, "x"); ax.xaxis.set_major_formatter(mt.FuncFormatter(hfmt)); ax.set_yticks(y); ax.set_yticklabels([l for _, l in pick], color=C.WHITE, fontsize=8); ax.grid(axis="y", visible=False); ax.set_xlim(0.8, 60000)
ax.set_xlabel("Posts in the prior 24h (grey) vs the last 24h (green), log scale", fontsize=7.5); ax.tick_params(labelsize=7.5); ax.set_title("Phrases that moved and phrases that did not")
save(fig, "g_keywords")

# 18. engagement share by class
cl = A["classes"]["interactions"]; names = {"news_aggregator": "News aggregators", "mid_account": "Mid accounts (50K-500K)", "official": "Official (Binance, CZ, Tether, Circle)", "small_account": "Small accounts (<50K)", "large_account": "Large accounts (500K+)", "elon": "Elon Musk"}
ck = sorted(cl, key=lambda k: -cl[k]); tot = sum(cl.values())
C.hbar("g_classes", [names[k] for k in ck], [cl[k] / tot * 100 for k in ck], w=3.3, h=2.3, color=C.BLUE, fmt=lambda v: f"{v:.0f}%", xlabel="Share of sampled engagements")
out["g_classes"] = os.path.join(C.OUT, "g_classes.png")

# 19. top creators
cw = A["creators_in_window"][:20]; ccol = {"official": C.GREEN, "news_aggregator": C.BLUE, "large_account": PURPLE, "mid_account": C.AMBER, "small_account": PINK, "elon": GREY}
fig, ax = plt.subplots(figsize=(6.8, 4.4)); y = list(range(len(cw)))[::-1]
ax.barh(y, [c["interactions"] for c in cw], color=[ccol[c["cls"]] for c in cw], height=0.62, zorder=3)
ax.set_yticks(y); ax.set_yticklabels(["@" + c["name"] for c in cw], color=C.WHITE, fontsize=8); ax.grid(axis="y", visible=False)
for yy, c in zip(y, cw): ax.text(c["interactions"] + 8e4, yy, f"{C.human(c['interactions'])}  ·  {c['posts']} posts  ·  {C.human(c['followers'])} followers  ·  {c['ipf']:.1f} eng/follower", va="center", fontsize=6.5, color=C.WHITE)
ax.set_xlim(0, cw[0]["interactions"] * 1.9); ax.xaxis.set_major_formatter(mt.FuncFormatter(lambda x, _: C.human(x))); ax.tick_params(labelsize=7.5)
for k, lab in names.items(): ax.scatter([], [], color=ccol[k], label=lab)
ax.legend(fontsize=6.5, ncol=3, loc="lower right"); ax.set_title("Top 20 accounts by engagements in the sampled posts, 20:24 to 01:00 UTC")
save(fig, "g_creators")

# 20. breakers scatter
br = [b for b in A["breakers"] if b["min_after"] <= 120]
# hand-placed labels: (creator, minute) -> (label x, label y, ha); every label gets a leader line to its dot
BLAB = {("spreekaway", 9): (2.5, 2.3e6, "left"), ("TreeNewsFeed", 15): (1.0, 8.2e5, "left"), ("bwenews", 15): (1.0, 1.75e5, "left"),
        ("rektober", 15): (1.0, 1.12e5, "left"), ("officer_secret", 17): (21.0, 1.02e5, "left"), ("TreeNewsFeed", 17): (1.0, 3.4e5, "left"),
        ("ASVPXILLZ", 18): (15.0, 1.3e6, "center"), ("crypto_banter", 20): (22.5, 4.6e5, "left"), ("StarPlatinum_", 34): (29.0, 7.6e5, "center"),
        ("ramonos", 40): (37.0, 1.0e6, "center"), ("TreeNewsFeed", 41): (36.0, 2.0e6, "right"), ("WatcherGuru", 44): (40.5, 1.55e6, "center"),
        ("KobeissiLetter", 50): (50.4, 1.02e6, "right"), ("cz_binance", 51): (46.5, 3.2e6, "right")}
fig, ax = plt.subplots(figsize=(6.8, 3.4))
for b in br:
    ax.scatter([b["min_after"]], [b["interactions"]], s=12 + 60 * math.log10(max(b["followers"], 1000) / 1000), color=ccol[b["cls"]], alpha=0.85, edgecolors=C.CARD, linewidths=0.5, zorder=3)
    pos = BLAB.get((b["creator"], b["min_after"]))
    if pos:
        ax.annotate("@" + b["creator"], (b["min_after"], b["interactions"]), xytext=(pos[0], pos[1]), textcoords="data", ha=pos[2], va="center", fontsize=6.3, color=C.WHITE, zorder=5,
                    arrowprops=dict(arrowstyle="-", color=C.MUTED, lw=0.45, shrinkA=1, shrinkB=3))
ax.set_yscale("log"); nominor(ax, "y"); ax.set_ylim(9e4, 5e6); ax.set_xlim(0, 54); ax.yaxis.set_major_locator(mt.FixedLocator([1e5, 2e5, 5e5, 1e6, 2e6, 5e6]))
ax.yaxis.set_major_formatter(mt.FuncFormatter(hfmt)); ax.set_xlabel("Minutes after 20:24 UTC", fontsize=7.5); ax.set_ylabel("Engagements (log)", fontsize=7.5); ax.tick_params(labelsize=7.5)
ax.axvline(51, color=C.GREEN, lw=0.8, ls=(0, (3, 3))); ax.text(50.6, 4.6e6, "CZ + @binance 21:15", color=C.GREEN, fontsize=6.8, ha="right", va="top")
for k, lab in (("official", "Official"), ("news_aggregator", "News aggregator"), ("large_account", "Large (500K+)"), ("mid_account", "Mid (50K-500K)"), ("small_account", "Small (<50K)")):
    ax.scatter([], [], color=ccol[k], s=22, label=lab)
ax.legend(fontsize=6.6, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.17), handletextpad=0.3, columnspacing=1.2)
ax.set_title("The first two hours: every sampled post over 100K engagements (dot size = followers)")
save(fig, "g_breakers")

# 21. official arc
# short hand-written labels: (account, HH:MM) -> (label, (label hour, minute), label y, ha)
OFF_LAB = {("cz_binance", "21:15"): ("Funds are safe", (21, 27), 3.9e6, "left"), ("cz_binance", "21:31"): ("life saver", (20, 57), 6.0e5, "right"),
           ("cz_binance", "22:23"): ("Loss might be a bit higher", (22, 36), 1.0e6, "left"), ("binance", "21:29"): ("User funds completely safe", (21, 40), 1.75e6, "left"),
           ("binance", "22:33"): ("Security checks", (22, 50), 1.9e5, "left"), ("binance", "23:22"): ("$2.54B verified", (23, 42), 1.2e6, "left"),
           ("binance", "00:13"): ("Will cover all losses", (0, 20), 1.35e5, "center")}
fig, ax = plt.subplots(figsize=(6.8, 3.0))
for who, col, lab in (("cz_binance", C.GREEN, "@cz_binance"), ("binance", C.BLUE, "@binance"), ("heyibinance", C.AMBER, "@heyibinance")):
    arc = [p for p in A.get(f"arc_{who}", []) if p["utc"] >= "Oct 29 20:00" or p["utc"].startswith("Oct 30")]
    xs = [datetime.datetime.strptime(p["utc"] + " 2026", "%b %d %H:%M %Y") for p in arc]; ys = [p["interactions"] for p in arc]
    ax.scatter(xs, ys, color=col, s=26, label=lab, zorder=3)
    for x_, y_, p in zip(xs, ys, arc):
        lab_ = OFF_LAB.get((who, p["utc"][-5:]))
        if lab_:
            txt, lx, ly, ha = lab_
            ax.annotate(txt, (x_, y_), xytext=(datetime.datetime(2026, 10, 29, *lx) if lx[0] >= 12 else datetime.datetime(2026, 10, 30, *lx), ly), textcoords="data", ha=ha, va="center",
                        fontsize=6.3, color=C.BODY, zorder=5, arrowprops=dict(arrowstyle="-", color=C.MUTED, lw=0.45, shrinkA=1, shrinkB=3.5))
ax.set_yscale("log"); nominor(ax, "y"); ax.set_ylim(4e3, 8e6); ax.yaxis.set_major_locator(mt.FixedLocator([1e4, 3e4, 1e5, 3e5, 1e6, 3e6])); ax.yaxis.set_major_formatter(mt.FuncFormatter(hfmt)); ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M")); ax.tick_params(labelsize=7.5)
ax.set_xlim(datetime.datetime(2026, 10, 29, 20, 0), datetime.datetime(2026, 10, 30, 1, 0))
ax.axvline(datetime.datetime(2026, 10, 29, 20, 24), color=C.AMBER, lw=0.8, ls=(0, (3, 3))); ax.text(datetime.datetime(2026, 10, 29, 20, 21), 6e3, "20:24 sweep", color=C.AMBER, fontsize=6.6, ha="right", va="bottom", rotation=90); ax.legend(fontsize=7, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.16)); ax.set_ylabel("Engagements per post (log)", fontsize=7.5)
ax.set_title("Every official post, 20:00 UTC Oct 29 to 01:00 UTC Oct 30")
save(fig, "g_official")

# 22. Bybit vs Binance hourly multiples
bb = A["comp"]["bybit_hourly"]["rows"]
fig, ax = plt.subplots(figsize=(6.8, 2.6))
ax.plot(range(len(FULL)), [h["x_base"] for h in FULL], marker="o", color=C.GREEN, lw=1.8, label="Binance, Oct 29 2026 (base 1.0M/h)")
ax.plot(range(len(bb)), [r["x"] for r in bb], marker="o", color=C.AMBER, lw=1.8, label="Bybit, Feb 21 2025 (base 459K/h)")
ax.set_xlabel("Hours since the hour of the first exploit transaction", fontsize=7.5); ax.set_ylabel("Engagements, multiple of own baseline", fontsize=7.5); ax.legend(fontsize=7.2); ax.tick_params(labelsize=7.5)
ax.set_title("Hour for hour against the Bybit hack")
save(fig, "g_bybit_vs")

# 23. comparables daily peak multiples
comp = A["comp"]; items = [("Binance\nOct 29 2026\n(3.6 event hrs)", 87152555 / 20586121, C.GREEN), ("Bybit hack\nFeb 2025", comp["bybit_feb2025"]["peak_x"], C.AMBER), ("Binance\nCZ plea\nNov 2023", comp["binance_nov2023"]["peak_x"], C.BLUE), ("Binance\nduring FTX\nNov 2022", comp["binance_nov2022"]["peak_x"], PURPLE), ("FTX collapse\nNov 2022", comp["ftx_nov2022"]["peak_x"], C.RED)]
fig, ax = plt.subplots(figsize=(6.8, 2.6)); x = list(range(len(items)))
ax.axhline(1, color=C.MUTED, lw=0.8, ls=(0, (3, 3)), zorder=2); ax.text(-0.45, 1.07, "1x = a normal day", ha="left", va="bottom", fontsize=6.6, color=C.MUTED)
for xx, (_, v, c) in zip(x, items):
    ax.plot([xx, xx], [1, v], color=c, lw=2.2, zorder=3, solid_capstyle="butt"); ax.scatter([xx], [v], s=70, color=c, edgecolors=C.CARD, linewidths=0.8, zorder=4)
    ax.text(xx + 0.09, v, f"{v:.1f}x", ha="left", va="center", fontsize=8, color=C.WHITE, fontweight=600)
ax.set_yscale("log"); ax.set_ylim(0.8, 220); ax.yaxis.set_major_locator(mt.FixedLocator([1, 2, 5, 10, 20, 50, 100, 200])); nominor(ax, "y")
ax.set_xlim(-0.5, len(items) - 0.5); ax.set_xticks(x); ax.set_xticklabels([l for l, _, _ in items], fontsize=6.8, color=C.WHITE); ax.grid(axis="x", visible=False); ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda x, _: f"{x:g}x")); ax.tick_params(axis="y", labelsize=7.5)
ax.set_ylabel("Peak-day multiple (log scale)", fontsize=7.5)
ax.set_title("Peak day as a multiple of the prior two weeks (Binance Oct 29 vs its 1-year median day)")
save(fig, "g_comp_daily")

# 24. Binance 1y daily
b1 = [r for r in A["binance_1y"]["series"] if r[0] < LAST_FULL]  # drop the partial Oct 30 day
fig, ax = plt.subplots(figsize=(6.8, 2.5)); tt = [ts(r[0]) for r in b1]; vv = [r[1] for r in b1]
ax.fill_between(tt, vv, color=C.BLUE, alpha=0.18); ax.plot(tt, vv, color=C.BLUE, lw=1.2)
for d, lab in (("2026-07-12", "Jul 12 high 161M"), ("2026-03-18", "Mar 18 152M"), ("2026-10-29", "Oct 29 87M\n(3.6 event hrs)")):
    i = next((j for j, r in enumerate(b1) if ts(r[0]).strftime("%Y-%m-%d") == d), None)
    if i is not None: ax.annotate(lab, (tt[i], vv[i]), xytext=(-40 if d != "2026-10-29" else -70, 10), textcoords="offset points", fontsize=6.8, color=C.WHITE, arrowprops=dict(arrowstyle="-", color=C.MUTED, lw=0.5))
ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda x, _: C.human(x))); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b")); ax.tick_params(labelsize=7.5); ax.set_ylabel("Engagements per UTC day", fontsize=7.5)
ax.set_title("Binance, daily engagements, last 365 days")
save(fig, "g_1y")

# 25. exchanges dominance
ex = A["exchanges"][:10]
C.hbar("g_exchanges", [e["title"].replace("Coinbase Global, Inc.", "Coinbase").replace("New York Stock Exchange", "NYSE") for e in ex], [e["dominance"] for e in ex], w=3.3, h=3.0, color=C.GREEN, fmt=lambda v: f"{v:.1f}%", xlabel="Share of exchange-category engagements, 24h")
out["g_exchanges"] = os.path.join(C.OUT, "g_exchanges.png")

# 26. crypto top with Binance inserted
# "REBATE" is a meaningless promo-token topic in the crypto category: dropped (the table drops it too)
ct = [c for c in A["cat_crypto_top15"][:9] if c["title"] != "REBATE"]; rows = [(c["title"], c["interactions"]) for c in ct] + [("Binance (exchange topic)", 114208335)]; rows.sort(key=lambda r: -r[1])
C.hbar("g_crypto_top", [r[0] for r in rows], [r[1] for r in rows], w=3.3, h=3.0, color=C.BLUE, fmt=C.human, xlabel="Engagements, last 24h",
       colors=[C.GREEN if r[0].startswith("Binance") else C.BLUE for r in rows])
out["g_crypto_top"] = os.path.join(C.OUT, "g_crypto_top.png")

# 27. claim ledger
# (minute after 20:24, $B, who, engagements, label position in data coords, ha)
_wazz = next((p for p in A["top_posts"] if p["creator"] == "WazzCrypto" and "5.57B" in p["text"]), None)
claims = [(15, 2.53, "@bwenews", 177000, (4, 4.3), "left"), (30, 2.77, "@DarkWebInformer", 176000, (22, 1.35), "center"), (32, 3.5, "@officer_secret", 204000, (39, 2.75), "left"),
          (62, 1.0, "@0xngmi (net, after freezes)", 621000, (70, 1.5), "left"), (78, 5.6, "@WatcherGuru", 1978837, (70, 3.7), "center"), (94, 5.7, "@KobeissiLetter", 2223858, (104, 4.6), "left")]
if _wazz: claims.insert(3, (48, 5.57, "@WazzCrypto", _wazz["interactions"], (34, 6.55), "center"))
fig, ax = plt.subplots(figsize=(6.8, 2.6))
for m, v, who, e, (tx, ty), ha in claims:
    ax.scatter([m], [v], s=20 + e / 12000, color=C.BLUE if "net" not in who else C.GREEN, alpha=0.8, edgecolors=C.CARD, zorder=3)
    # two single-line texts: matplotlib drops font features on multi-line text, which would turn "0x" into "0×"
    lead = dict(arrowstyle="-", color=C.MUTED, lw=0.5, shrinkA=1, shrinkB=4)  # leader leaves from the line nearest the dot
    ax.annotate(who, (m, v), xytext=(tx, ty), textcoords="data", ha=ha, va="bottom", fontsize=6.3, color=C.WHITE, zorder=5, arrowprops=None if ty > v else lead)
    ax.annotate(f"${v:.2f}B · {C.human(e)}", (m, v), xytext=(tx, ty), textcoords="data", ha=ha, va="top", fontsize=6.3, color=C.WHITE, zorder=5, arrowprops=lead if ty > v else None)
ax.set_xlim(0, 150); ax.set_ylim(0, 7.3); ax.set_xlabel("Minutes after 20:24 UTC", fontsize=7.5); ax.set_ylabel("Figure in the post ($B)", fontsize=7.5); ax.tick_params(labelsize=7.5)
ax.set_title("The loss figure climbed with every retelling, and the biggest numbers drew the most engagement (dot size)")
save(fig, "g_claims")

# 28. cumulative engagements and creators
# two stacked panels on a shared hour axis, so bar labels never meet the creators line
fig, (ax, ax2) = plt.subplots(2, 1, figsize=(6.8, 2.9), sharex=True, gridspec_kw=dict(height_ratios=[2.1, 1], hspace=0.12)); cum = 0; cums = []
for h in FULL: cum += h["interactions"]; cums.append(cum)
ax.bar(LAB[:-1], cums, color=C.GREEN, width=0.6, zorder=3)
for i, v in enumerate(cums): ax.text(i, v + max(cums) * 0.025, C.human(v), ha="center", va="bottom", fontsize=7.2, color=C.WHITE, fontweight=600)
ax.set_ylim(0, max(cums) * 1.18); ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda x, _: f"{x/1e6:g}M" if x else "0")); ax.tick_params(labelsize=7.5); ax.grid(axis="x", visible=False)
ax.set_ylabel("Cumulative\nengagements", fontsize=7.2)
ca = [h["contributors_active"] for h in FULL]
ax2.plot(LAB[:-1], ca, color=C.WHITE, marker="o", ms=3.5, lw=1.4, zorder=3); ax2.set_ylim(0, max(ca) * 1.45)
for i, v in enumerate(ca): ax2.text(i, v + max(ca) * 0.1, f"{v/1000:.1f}K", ha="center", va="bottom", fontsize=6.8, color=C.WHITE)
ax2.yaxis.set_major_locator(mt.MultipleLocator(10000)); ax2.yaxis.set_major_formatter(mt.FuncFormatter(lambda x, _: f"{x/1000:g}K" if x else "0")); ax2.tick_params(labelsize=7.5); ax2.grid(axis="x", visible=False)
ax2.set_ylabel("Active creators\nin the hour", fontsize=7.2); ax.set_title("Still climbing at the data cut")
save(fig, "g_cum")

# 29. scenarios: Bybit decay vs FTX path scaled to Binance day 1 (labelled scenarios)
byb = [r[1] for r in comp["bybit_feb2025"]["series"]]; bybd = [r[0] for r in comp["bybit_feb2025"]["series"]]
i0 = bybd.index("02-21"); byb_path = [x / byb[i0 + 1] for x in byb[i0:i0 + 8]]
ftx = [r[1] for r in comp["ftx_nov2022"]["series"]]; ftxd = [r[0] for r in comp["ftx_nov2022"]["series"]]
j0 = ftxd.index("11-08"); ftx_path = [x / max(ftx[j0:j0 + 2]) for x in ftx[j0:j0 + 8]]
fig, ax = plt.subplots(figsize=(6.8, 2.5))
ax.plot(range(len(byb_path)), byb_path, marker="o", color=C.AMBER, lw=1.6, label="Scenario A: Bybit Feb 2025 shape (peak day 2, decays)")
ax.plot(range(len(ftx_path)), ftx_path, marker="o", color=C.RED, lw=1.6, label="Scenario B: FTX Nov 2022 shape (second wave)")
ax.set_xlabel("Days from event day (day 0 = event day)", fontsize=7.5); ax.set_ylabel("Daily engagements, share of peak", fontsize=7.5); ax.legend(fontsize=7); ax.tick_params(labelsize=7.5)
ax.set_title("Two historical shapes the next week could follow (scenarios, not forecasts)")
save(fig, "g_scenarios")

json.dump(out, open(os.path.join(HERE, "charts_index.json"), "w"), indent=1)
print("charts:", len(out))

# ---- 30. the operator's day (verified on-chain) and the hijack window
import matplotlib.patches as mpatches
OPS = [("10-28 07:39", "Tornado 0.1 ETH", "fund"), ("10-28 08:53", "Tornado 0.1 ETH", "fund"), ("10-29 02:28", "deploy sweeper v1", "prep"), ("10-29 08:23", "Tornado 0.1 ETH", "fund"),
       ("10-29 13:51", "delegate 2 test wallets", "rehearse"), ("10-29 14:19", "sweep test wallets", "rehearse"), ("10-29 15:59", "deploy sweeper v2", "prep"), ("10-29 16:20", "delegate test wallet 3", "rehearse"),
       ("10-29 16:30", "sweep + withdraw (16:47)", "rehearse"), ("10-29 18:20", "gas 1.08 ETH arrives", "fund"), ("10-29 20:20", "50 auths on Binance 14", "attack"), ("10-29 20:24", "sweep: 63 tokens + 167K ETH", "attack"),
       ("10-29 20:41", "780M USDC via Hot Wallet 34", "attack"), ("10-29 20:59", "43M USDC", "attack"), ("10-29 21:04", "re-sweep 3.9M USDT", "attack"), ("10-29 21:44", "re-sweep 200.4M USDT", "attack"), ("10-29 22:39", "long-tail basket, 2nd receiver", "attack"), ("10-30 00:10", "Binance 14 revokes", "revoke")]
col = {"fund": C.MUTED, "prep": C.BLUE, "rehearse": C.AMBER, "attack": C.RED, "revoke": C.GREEN}
fig, ax = plt.subplots(figsize=(6.8, 4.2))
t0 = datetime.datetime(2026, 10, 28, 0, 0, tzinfo=UTC)
for i, (ts_, lab, kind) in enumerate(OPS):
    d = datetime.datetime.strptime("2026-" + ts_, "%Y-%m-%d %H:%M").replace(tzinfo=UTC); h = (d - t0).total_seconds() / 3600
    ax.scatter([h], [len(OPS) - i], color=col[kind], s=42, zorder=3, edgecolors=C.CARD, linewidths=0.5)
    ax.text(h + 0.6, len(OPS) - i, f"{ts_[6:]}  {lab}", va="center", fontsize=6.8, color=C.WHITE)
ax.axvline((datetime.datetime(2026, 10, 29, 20, 24, tzinfo=UTC) - t0).total_seconds() / 3600, color=C.RED, lw=0.8, ls=(0, (3, 3)))
ax.set_yticks([]); ax.set_xlim(0, 52); ax.set_xlabel("Hours from 00:00 UTC Oct 28", fontsize=7.5); ax.tick_params(labelsize=7.5); ax.grid(axis="y", visible=False)
ax.legend(handles=[mpatches.Patch(color=c, label=k) for k, c in col.items()], fontsize=7, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.12))
ax.set_title("The operator's day: every transaction of 0x7C86 and its funders, verified on-chain")
save(fig, "g_operator_day")

# hijack window: sweeps vs deposits vs revocation
fig, ax = plt.subplots(figsize=(6.8, 2.6))
ev = [("20:20:59", "delegation", 0.0, C.AMBER), ("20:24:23", "sweep", 2800, C.RED), ("20:41:23", "780M USDC", 780, C.RED), ("20:59:47", "43M USDC", 43, C.RED), ("21:04:23", "3.9M USDT", 4, C.RED), ("21:44:11", "204M USDT+", 204, C.RED), ("22:39:35", "basket >=7.5M", 7.5, C.RED), ("00:10:35", "revocation", 0.0, C.GREEN)]
base = datetime.datetime(2026, 10, 29, 20, 0, tzinfo=UTC)
for ts_, lab, val, c in ev:
    hh, mm, ss = map(int, ts_.split(":")); d = datetime.datetime(2026, 10, 29 if hh >= 20 else 30, hh, mm, ss, tzinfo=UTC); x = (d - base).total_seconds() / 60
    ax.bar([x], [max(val, 1)], width=4, color=c, zorder=3); ax.text(x + (6 if val == 0 else 0), max(val, 1) * (1.15 if val else 2.2), f"{ts_[:5]}\n{lab}", ha="center" if val else "left", fontsize=6.3, color=C.WHITE)
ax.set_yscale("log"); ax.set_ylim(0.8, 9000); ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f"${v/1000:g}B" if v >= 1000 else f"${v:g}M")); ax.set_xlabel("Minutes after 20:00 UTC Oct 29", fontsize=7.5); ax.tick_params(labelsize=7.5)
ax.axvspan(21, 250.6, color=C.AMBER, alpha=0.08); ax.text(130, 2000, "delegation live 3h 50m: 533 deposit transfers arrived", ha="center", fontsize=7, color=C.AMBER)
ax.axvline(32, color=C.BLUE, lw=0.8, ls=(0, (3, 3))); ax.text(33, 12, "first public\npost 20:32", fontsize=6.5, color=C.BLUE)
ax.set_title("What left Binance 14 and Hot Wallet 34 after the delegation, by minute (explorer-visible lines)")
save(fig, "g_hijack_window")
json.dump(out, open(os.path.join(HERE, "charts_index.json"), "w"), indent=1); print("charts:", len(out))

# ---- 32/33. fund flow map and current positions
FS = json.load(open(os.path.join(ROOT, "onchain", "flow_summary.json")))
from matplotlib.path import Path as MPath
import matplotlib.patches as mpatches
def band(ax, x0, y0, h0, x1, y1, h1, color, alpha=0.55):
    xm = (x0 + x1) / 2
    verts = [(x0, y0), (xm, y0), (xm, y1), (x1, y1), (x1, y1 + h1), (xm, y1 + h1), (xm, y0 + h0), (x0, y0 + h0), (x0, y0)]
    codes = [MPath.MOVETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4, MPath.LINETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4, MPath.CLOSEPOLY]
    ax.add_patch(mpatches.PathPatch(MPath(verts, codes), facecolor=color, edgecolor="none", alpha=alpha, zorder=2))
fig, ax = plt.subplots(figsize=(6.8, 4.6)); ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off"); ax.set_facecolor(C.CARD)
# left: sources by chain (USD millions, gross = held + frozen attributable)
SRC = [("Ethereum", 0, C.BLUE), ("Bitcoin", 1413.2, C.AMBER), ("Tron", 312.7, "#F472B6"), ("XRP Ledger", 284.8, PURPLE), ("Solana", 92.2, GREY), ("Arbitrum", 30.5, "#22D3EE")]
# simplify: ethereum gross = ETH held (975.6) + XAUt 50.2 + frozen ERC-20 (1175.5+823+175+60+27.8)
SRC[0] = ("Ethereum", 975.6 + 50.2 + 1175.5 + 823 + 175 + 60 + 27.8, C.BLUE)
DST = [("Frozen or recovered", FS["totals"]["frozen_or_recovered_usd_m"], C.GREEN), ("Unfrozen, traced", FS["totals"]["held_unfrozen_usd_m"], C.RED)]
# flows (source -> dest) in $M
FLOWS = {("Ethereum", "Frozen or recovered"): 1175.5 + 823 + 175 + 60 + 27.8, ("Ethereum", "Unfrozen, traced"): 975.6 + 50.2, ("Bitcoin", "Unfrozen, traced"): 1413.2, ("Tron", "Frozen or recovered"): 312.7, ("XRP Ledger", "Unfrozen, traced"): 284.8, ("Solana", "Unfrozen, traced"): 92.2, ("Arbitrum", "Frozen or recovered"): 30.5}
tot = sum(v for _, v, _ in SRC); scale = 8.6 / tot; gap = 0.18
y = 9.6; spos = {}; labels = []
for name, v, col in SRC:
    h = v * scale; y -= h; spos[name] = (y, h, col); ax.add_patch(mpatches.Rectangle((1.2, y), 0.5, h, color=col, zorder=3)); labels.append([y + h / 2, f"{name}  ${v/1000:.2f}B" if v >= 1000 else f"{name}  ${v:.0f}M", col]); y -= gap
# push labels apart (min 0.42 units) from the bottom up
labels.sort(key=lambda l: l[0]); last = -9
for l in labels:
    if l[0] - last < 0.42: l[0] = last + 0.42
    last = l[0]
for ly, lab, col in labels: ax.text(1.1, ly, lab, ha="right", va="center", fontsize=7, color=C.WHITE)
dtot = sum(v for _, v, _ in DST); dscale = 8.6 / dtot; y = 9.6; dpos = {}
for name, v, col in DST:
    h = v * dscale; y -= h; dpos[name] = (y, h, col); ax.add_patch(mpatches.Rectangle((8.3, y), 0.5, h, color=col, zorder=3)); ax.text(8.95, y + h / 2, f"{name}\n${v/1000:.2f}B", ha="left", va="center", fontsize=7.5, color=C.WHITE, fontweight=600); y -= gap * 2
soff = {k: v[0] + v[1] for k, v in spos.items()}; doff = {k: v[0] + v[1] for k, v in dpos.items()}
for (s, d), v in sorted(FLOWS.items(), key=lambda kv: -kv[1]):
    h0 = v * scale; h1 = v * dscale; soff[s] -= h0; doff[d] -= h1
    band(ax, 1.7, soff[s], h0, 8.3, doff[d], h1, spos[s][2], alpha=0.5)
ax.text(5, 9.85, f"Gross traced: ${tot/1000:.2f}B at {FS['cut_utc']} prices. Widths are USD. Left: chain the funds left from. Right: status now.", ha="center", fontsize=6.8, color=C.MUTED)
ax.set_title("Where the funds went, by chain and status (LunarCrush on-chain trace)")
save(fig, "g_flow")
# positions bar
def lab(x): w = x["where"].split(" (")[0].replace("15 fresh addresses, 13 holding exactly 1,000 BTC", "15 fresh addresses").replace("moving: ", "")[:26]; return f"{x['asset']}  {w}"
rows = [(lab(h), h["usd"], C.RED if "Unfrozen" in h["status"] else C.AMBER) for h in FS["held"]] + [(lab(f), f["usd"], C.GREEN) for f in FS["frozen"]]
rows.sort(key=lambda r: -r[1])
fig, ax = plt.subplots(figsize=(6.8, 5.2)); y = list(range(len(rows)))[::-1]
ax.barh(y, [r[1] for r in rows], color=[r[2] for r in rows], height=0.62, zorder=3)
ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], color=C.WHITE, fontsize=7.5); ax.grid(axis="y", visible=False)
for yy, r in zip(y, rows): ax.text(r[1] + 12, yy, f"${r[1]:,.0f}M", va="center", fontsize=6.8, color=C.WHITE)
ax.set_xlim(0, max(r[1] for r in rows) * 1.25); ax.xaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f"${v/1000:.1f}B" if v >= 1000 else f"${v:.0f}M")); ax.tick_params(labelsize=7.5)
ax.scatter([], [], color=C.RED, label="unfrozen, in traced addresses"); ax.scatter([], [], color=C.GREEN, label="frozen or recovered"); ax.scatter([], [], color=C.AMBER, label="status unknown"); ax.legend(fontsize=7, loc="lower right")
ax.set_title(f"Every position we could verify, at {FS['cut_utc']} prices")
save(fig, "g_positions")
json.dump(out, open(os.path.join(HERE, "charts_index.json"), "w"), indent=1); print("charts:", len(out))
