#!/usr/bin/env python3
"""Compute every metric for the Binance hack report from raw/ into analysis.json and print a digest.
Event start: 2026-10-29 20:24 UTC (first exploit tx). Hourly buckets are UTC hour starts."""
import json, os, re, glob, datetime, statistics, unicodedata
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, "raw")
T0 = 1793304000          # 2026-10-29 20:00 UTC bucket (event hour)
EVENT_TS = 1793305440    # 20:24 UTC
UTC = datetime.UTC
def ld(name):
    p = os.path.join(R, name + ".json")
    if not os.path.exists(p): return None
    d = json.load(open(p)); return d.get("data", d) if isinstance(d, dict) else d
def hhmm(ts): return datetime.datetime.fromtimestamp(ts, UTC).strftime("%H:%M")
def dstr(ts): return datetime.datetime.fromtimestamp(ts, UTC).strftime("%b %d %H:%M")
A = {"meta": {"event_start_utc": "2026-10-29 20:24", "pulled_utc": None}}

# ---------- 1. Binance hourly: baseline, multiples, cumulative
ts = ld("ts_binance_1w_hour")
A["meta"]["pulled_utc"] = dstr(ts[-1]["time"]) + " (last bucket, partial)"
pre = [r for r in ts if r["time"] < T0]; post = [r for r in ts if r["time"] >= T0]
def base(key, rows=pre, agg=statistics.mean): return agg([r[key] for r in rows if r.get(key) is not None])
BASE = {k: base(k) for k in ("interactions", "posts_created", "contributors_created", "posts_active", "contributors_active", "sentiment", "spam")}
# same-hour-of-day baseline (20:00-01:00 UTC on the prior 6 days)
sameh = defaultdict(list)
for r in pre: sameh[datetime.datetime.fromtimestamp(r["time"], UTC).hour].append(r)
hourly = []
for r in post:
    h = datetime.datetime.fromtimestamp(r["time"], UTC).hour
    sb = statistics.mean([x["interactions"] for x in sameh[h]]) if sameh[h] else BASE["interactions"]
    hourly.append({"utc": dstr(r["time"]), "interactions": r["interactions"], "x_base": r["interactions"] / BASE["interactions"], "x_samehour": r["interactions"] / sb,
                   "posts_created": r["posts_created"], "x_posts": r["posts_created"] / BASE["posts_created"], "contributors_created": r["contributors_created"],
                   "contributors_active": r["contributors_active"], "posts_active": r["posts_active"], "sentiment": r["sentiment"], "spam": r["spam"], "partial": r is post[-1]})
A["binance_hourly"] = {"baseline": BASE, "post": hourly, "pre_series": [(r["time"], r["interactions"], r["sentiment"], r["posts_created"], r["contributors_created"]) for r in ts]}
full = [h for h in hourly if not h["partial"]]
A["binance_hourly"]["cum_interactions_full_hours"] = sum(h["interactions"] for h in full)
A["binance_hourly"]["cum_posts_created"] = sum(h["posts_created"] for h in full)
A["binance_hourly"]["cum_new_contributors"] = sum(h["contributors_created"] for h in full)
A["binance_hourly"]["peak"] = max(hourly, key=lambda h: h["interactions"])
A["binance_hourly"]["week_pre_total"] = sum(r["interactions"] for r in pre)
A["binance_hourly"]["pre_max_hour"] = max(pre, key=lambda r: r["interactions"])["interactions"]
A["binance_hourly"]["sent_pre_mean"] = BASE["sentiment"]; A["binance_hourly"]["sent_min"] = min(h["sentiment"] for h in hourly)

# ---------- 2. Per-network hourly lag
NETS = ["twitter", "tiktok", "youtube", "reddit", "instagram", "news"]
netlag = {}
for n in NETS:
    s = ld(f"ts_binance_1w_hour_{n}")
    if not s: continue
    p_ = [r for r in s if r["time"] < T0]; q_ = [r for r in s if r["time"] >= T0]
    bi = statistics.mean([r["interactions"] for r in p_]) or 1; bp = statistics.mean([r["posts_created"] for r in p_]) or 1
    rows = [{"utc": hhmm(r["time"]), "interactions": r["interactions"], "x": r["interactions"] / bi, "posts_created": r["posts_created"], "xp": r["posts_created"] / bp, "sentiment": r.get("sentiment"), "contributors_created": r.get("contributors_created")} for r in q_]
    first3x = next((r["utc"] for r in rows if r["xp"] >= 3), None); first3xi = next((r["utc"] for r in rows if r["x"] >= 3), None)
    pk = max(rows[:-1] or rows, key=lambda r: r["posts_created"])
    netlag[n] = {"base_int_h": bi, "base_posts_h": bp, "rows": rows, "first_3x_posts": first3x, "first_3x_int": first3xi, "peak_posts_utc": pk["utc"], "peak_posts_x": pk["xp"],
                 "post_total_full": sum(r["posts_created"] for r in rows[:-1]), "int_total_full": sum(r["interactions"] for r in rows[:-1]),
                 "sent_pre": statistics.mean([r["sentiment"] for r in p_ if r.get("sentiment")]), "sent_post": statistics.mean([r["sentiment"] for r in q_ if r.get("sentiment")])}
A["network_lag"] = netlag

# ---------- 3. Contagion: related topics
REL = ["bnb", "bitcoin", "ethereum", "tether", "usdc", "hyperliquid", "coinbase", "okx", "bybit", "kraken", "solana", "xrp", "tornado", "crypto", "coin", "hood", "mstr", "gold"]
DISP = {"bnb": "BNB", "bitcoin": "Bitcoin", "ethereum": "Ethereum", "tether": "Tether (USDT)", "usdc": "USDC", "hyperliquid": "Hyperliquid", "coinbase": "Coinbase", "okx": "OKX", "bybit": "Bybit", "kraken": "Kraken",
        "solana": "Solana", "xrp": "XRP", "tornado": "Tornado Cash", "crypto": "Crypto (all)", "coin": "$COIN (Coinbase stock)", "hood": "$HOOD (Robinhood)", "mstr": "$MSTR (Strategy)", "gold": "Gold", "binance": "Binance"}
cont = []
for t in ["binance"] + REL:
    s = ld(f"ts_{t}_1w_hour")
    if not s: continue
    p_ = [r for r in s if r["time"] < T0]; q_ = [r for r in s if T0 <= r["time"] < T0 + 5 * 3600]
    if not p_ or not q_: continue
    bi = statistics.mean([r["interactions"] for r in p_]); bp = statistics.mean([r["posts_created"] for r in p_]) or 1; bc = statistics.mean([r["contributors_created"] for r in p_]) or 1
    sp = statistics.mean([r["sentiment"] for r in p_ if r.get("sentiment")]); sq = statistics.mean([r["sentiment"] for r in q_ if r.get("sentiment")])
    pk = max(q_, key=lambda r: r["interactions"])
    cont.append({"topic": t, "display": DISP[t], "base_int_h": bi, "peak_int_h": pk["interactions"], "peak_x": pk["interactions"] / bi, "peak_utc": hhmm(pk["time"]),
                 "x_posts_5h": sum(r["posts_created"] for r in q_) / (bp * 5), "x_newcreators_5h": sum(r["contributors_created"] for r in q_) / (bc * 5),
                 "sent_pre": sp, "sent_post": sq, "sent_delta": sq - sp, "int_5h": sum(r["interactions"] for r in q_),
                 "hours": [{"utc": hhmm(r["time"]), "x": r["interactions"] / bi, "sentiment": r["sentiment"]} for r in q_]})
A["contagion"] = sorted(cont, key=lambda c: -c["peak_x"])

# ---------- 4. Keyword narratives
KW = ["binance_hack", "binance_hacked", "SAFU", "cz", "user_funds_are_safe", "binance_withdrawals", "hot_wallet", "EIP7702", "tether_freeze", "crypto_hack", "not_your_keys", "largest_hack", "bank_run", "bybit_hack", "lazarus", "north_korea", "withdraw", "binance_down"]
kws = {}
for k in KW:
    snap = ld(f"kw_{k}"); s = ld(f"kwts_{k}_1w_hour")
    if not snap: continue
    m = snap.get("metrics", {}); so = snap.get("social", {}); se = snap.get("sentiment", {})
    row = {"display": k.replace("_", " "), "posts_24h": m.get("posts_active", {}).get("24h"), "posts_prev": m.get("posts_active", {}).get("24h_previous"),
           "creators_24h": m.get("contributors_active", {}).get("24h"), "creators_prev": m.get("contributors_active", {}).get("24h_previous"),
           "int_24h": m.get("interactions", {}).get("24h"), "int_prev": m.get("interactions", {}).get("24h_previous"),
           "sent_by_net": se.get("network"), "net_posts": so.get("network_posts_active"), "net_int": so.get("network_interactions"),
           "hourly": [{"utc": dstr(r["time"]), "posts_created": r.get("posts_created"), "interactions": r.get("interactions"), "contributors_created": r.get("contributors_created"), "sentiment": r.get("sentiment")} for r in (s or []) if r["time"] >= T0 - 3600]}
    if row["hourly"]:
        pk = max(row["hourly"], key=lambda h: h["posts_created"] or 0); row["peak_utc"] = pk["utc"]; row["peak_posts"] = pk["posts_created"]
        row["first_utc"] = next((h["utc"] for h in row["hourly"] if (h["posts_created"] or 0) >= 20), None)
    kws[k] = row
A["keywords"] = kws

# ---------- 5. Posts: who broke it, classes, themes, languages, minute cumulative
posts = {}
for f in glob.glob(os.path.join(R, "posts_*.json")) + glob.glob(os.path.join(R, "kwposts_*.json")) + glob.glob(os.path.join(R, "creatorposts_*.json")):
    d = json.load(open(f)); d = d.get("data", d) if isinstance(d, dict) else d
    for p in d or []:
        if p.get("id") and p.get("post_created"): posts[(p.get("post_type"), p["id"])] = p
PL = list(posts.values())
ev = [p for p in PL if p["post_created"] >= EVENT_TS - 600 and p["post_created"] < T0 + 6 * 3600]
def text(p): return ((p.get("post_title") or "") + " " + (p.get("post_description") or "") + " " + (p.get("post_extraText") or "")).lower()
BIN = re.compile(r"binance|\bcz\b|\bbnb\b|tether|usdt|circle|usdc|hack|exploit|drain|safu|hot wallet|withdraw")
ev = [p for p in ev if BIN.search(text(p))]
ev.sort(key=lambda p: p["post_created"])
A["posts_meta"] = {"unique_posts_loaded": len(PL), "event_window_posts": len(ev)}
OFFICIAL = {"binance", "cz_binance", "heyibinance", "richardteng", "paoloardoino", "tether_to", "jerallaire", "circle", "binanceus", "binance_us", "aave", "stani"}
AGG = {"watcherguru", "kobeissiletter", "treenewsfeed", "spectatorindex", "cointelegraph", "coindesk", "whale_alert", "lookonchain", "peckshieldalert", "zachxbt", "unusual_whales", "bitcoinmagazine", "coinbureau", "decryptmedia", "theblock__", "wublockchain", "solidintel_x", "arkham", "bubblemaps", "certik", "certikalert", "cyvers_", "blockaid_", "db", "disclosetv", "bnonews", "breakingnews"}
def cls(p):
    n = (p.get("creator_name") or "").lower(); f = p.get("creator_followers") or 0
    if n in OFFICIAL: return "official"
    if n in AGG or "news" in n or "alert" in n or "intel" in n: return "news_aggregator"
    if n == "elonmusk": return "elon"
    if f >= 500000: return "large_account"
    if f >= 50000: return "mid_account"
    return "small_account"
THEMES = [("hack confirmed / drained", r"hack|exploit|drain|stolen|compromis"), ("funds safe / SAFU", r"safu|funds are safe|funds safe|fully cover|will cover|covered"),
          ("freeze (Tether/Circle)", r"freez|froze|blacklist"), ("withdrawals / bank run", r"withdraw|bank run|get your (money|funds) out|pause"),
          ("insolvency / FTX comparison", r"insolven|\bftx\b|\bsbf\b|bankrupt|proof of reserve"), ("not your keys / self custody", r"not your keys|self[- ]custody|cold wallet|hardware wallet|ledger"),
          ("attribution (Lazarus / DPRK)", r"lazarus|north korea|dprk|inside job|insider"), ("vector (EIP-7702 / hot wallet)", r"7702|hot wallet|delegat|eoa|contract call"),
          ("price / liquidations", r"liquidat|dump|crash|\$7[0-9],?[0-9]{3}|bitcoin (drops|falls|sinks)|btc (drops|falls)"), ("buy the dip / bullish", r"buy the dip|bullish|discount|buying|accumulat"),
          ("largest hack ever", r"largest|biggest|record")]
theme = {t: {"posts": 0, "interactions": 0, "first_utc": None, "by_hour": Counter()} for t, _ in THEMES}
cl = Counter(); cli = Counter(); lang = Counter(); langi = Counter(); minute = defaultdict(int); byhour_type = defaultdict(Counter)
def script(s):
    c = Counter()
    for ch in s:
        if ch.isalpha():
            try: nm = unicodedata.name(ch).split()[0]
            except ValueError: continue
            c[nm] += 1
    if not c: return "unknown"
    top = c.most_common(1)[0][0]
    return {"LATIN": "Latin", "CYRILLIC": "Cyrillic", "CJK": "Chinese", "HIRAGANA": "Japanese", "KATAKANA": "Japanese", "HANGUL": "Korean", "ARABIC": "Arabic", "THAI": "Thai", "DEVANAGARI": "Hindi", "BENGALI": "Bengali", "GREEK": "Greek", "HEBREW": "Hebrew"}.get(top, top.title())
for p in ev:
    c = cls(p); it = p.get("interactions_total") or 0; cl[c] += 1; cli[c] += it
    tx = text(p); hr = hhmm((p["post_created"] // 3600) * 3600)
    byhour_type[hr][p["post_type"]] += 1
    for t, rx in THEMES:
        if re.search(rx, tx):
            theme[t]["posts"] += 1; theme[t]["interactions"] += it; theme[t]["by_hour"][hr] += 1
            if not theme[t]["first_utc"]: theme[t]["first_utc"] = dstr(p["post_created"])
    sc = script((p.get("post_title") or "")[:200]); lang[sc] += 1; langi[sc] += it
    if p["post_created"] >= EVENT_TS: minute[(p["post_created"] - EVENT_TS) // 60] += it
for t in theme: theme[t]["by_hour"] = dict(theme[t]["by_hour"])
A["themes"] = theme; A["classes"] = {"posts": dict(cl), "interactions": dict(cli)}; A["languages"] = {"posts": dict(lang), "interactions": dict(langi)}
A["types_by_hour"] = {h: dict(c) for h, c in byhour_type.items()}
cum = 0; mc = []
for m in range(0, 300):
    cum += minute.get(m, 0); mc.append(cum)
A["minute_cum_interactions"] = mc
# breakers: earliest posts >= 100K interactions
A["breakers"] = [{"utc": dstr(p["post_created"]), "min_after": round((p["post_created"] - EVENT_TS) / 60), "creator": p.get("creator_name"), "followers": p.get("creator_followers"), "interactions": p.get("interactions_total"), "type": p.get("post_type"), "cls": cls(p), "text": (p.get("post_title") or "")[:220].replace("\n", " ")}
                 for p in ev if (p.get("interactions_total") or 0) >= 100000][:40]
A["top_posts"] = [{"utc": dstr(p["post_created"]), "creator": p.get("creator_name"), "followers": p.get("creator_followers"), "interactions": p.get("interactions_total"), "type": p.get("post_type"), "sentiment": p.get("post_sentiment"), "cls": cls(p), "link": p.get("post_link"), "text": (p.get("post_title") or "")[:300].replace("\n", " ")}
                  for p in sorted(ev, key=lambda p: -(p.get("interactions_total") or 0))[:60]]
A["top_by_network"] = {}
for n in ["tiktok-video", "youtube-video", "reddit-post", "news", "instagram-post"]:
    A["top_by_network"][n] = [{"utc": dstr(p["post_created"]), "creator": p.get("creator_name"), "followers": p.get("creator_followers"), "interactions": p.get("interactions_total"), "sentiment": p.get("post_sentiment"), "text": (p.get("post_title") or "")[:200].replace("\n", " ")}
                              for p in sorted([q for q in ev if q["post_type"] == n], key=lambda p: -(p.get("interactions_total") or 0))[:8]]
A["sentiment_dist"] = dict(Counter(p.get("post_sentiment") for p in ev))
# interactions per follower (reach efficiency) for creators with >= 3 posts in window
cr = defaultdict(lambda: {"posts": 0, "interactions": 0, "followers": 0, "first": None, "cls": None})
for p in ev:
    n = p.get("creator_name") or "?"; cr[n]["posts"] += 1; cr[n]["interactions"] += p.get("interactions_total") or 0; cr[n]["followers"] = p.get("creator_followers") or 0; cr[n]["cls"] = cls(p)
    cr[n]["first"] = min(cr[n]["first"] or p["post_created"], p["post_created"])
A["creators_in_window"] = sorted([{"name": n, **v, "first_utc": dstr(v["first"]), "ipf": v["interactions"] / max(v["followers"], 1)} for n, v in cr.items()], key=lambda r: -r["interactions"])[:40]

# ---------- 6. CZ and Binance official arcs
for who in ["cz_binance", "binance", "heyibinance", "richardteng", "elonmusk", "paoloardoino"]:
    d = ld(f"creatorposts_{who}")
    if d: A[f"arc_{who}"] = [{"utc": dstr(p["post_created"]), "interactions": p.get("interactions_total"), "sentiment": p.get("post_sentiment"), "text": (p.get("post_title") or "")[:200].replace("\n", " ")} for p in sorted(d, key=lambda p: p["post_created"]) if p["post_created"] >= T0 - 7200]

# ---------- 7. Creators tables (topic-level)
for t in ["binance", "bnb", "bitcoin"]:
    d = ld(f"creators_{t}")
    if d: A[f"creators_{t}"] = [{"name": c["name"], "network": c["network"], "followers": c["followers"], "posts": c["posts_active"], "interactions": c["interactions"], "ipf": c["interactions"] / max(c["followers"], 1)} for c in d[:30]]
cb = A.get("creators_binance", [])
A["creator_concentration"] = {"top1_share": cb[0]["interactions"] / 114208335 if cb else None, "top10_share": sum(c["interactions"] for c in cb[:10]) / 114208335 if cb else None, "topic_total_24h": 114208335}

# ---------- 8. Snapshots: binance + related topic 24h metrics, networks, sentiment
snaps = {}
for t in ["binance"] + REL:
    s = ld(f"topic_{t}")
    if not s: continue
    m = s.get("metrics", {}); so = s.get("social", {}); se = s.get("sentiment", {})
    snaps[t] = {"display": DISP[t], "int_24h": m.get("interactions", {}).get("24h"), "int_prev": m.get("interactions", {}).get("24h_previous"), "int_1y_high": m.get("interactions", {}).get("high"), "int_1y_high_date": m.get("interactions", {}).get("high_date"),
                "posts_24h": m.get("posts_active", {}).get("24h"), "posts_prev": m.get("posts_active", {}).get("24h_previous"), "creators_24h": m.get("contributors_active", {}).get("24h"), "creators_prev": m.get("contributors_active", {}).get("24h_previous"),
                "newcreators_24h": m.get("contributors_created", {}).get("24h"), "newcreators_prev": m.get("contributors_created", {}).get("24h_previous"),
                "net_int": so.get("network_interactions"), "net_posts": so.get("network_posts_active"), "net_sent": se.get("network"), "sent_posts": se.get("posts_active"), "sent_int": se.get("interactions"), "ai_summary": s.get("ai_summary")}
A["snapshots"] = snaps

# ---------- 9. Comparables
def daily_stats(name, event_day_str):
    s = ld(name)
    if not s: return None
    ev_day = int(datetime.datetime.strptime(event_day_str, "%Y-%m-%d").replace(tzinfo=UTC).timestamp())
    pre_ = [r for r in s if r["time"] < ev_day][-14:]; post_ = [r for r in s if r["time"] >= ev_day][:10]
    if not pre_ or not post_: return None
    b = statistics.mean([r["interactions"] for r in pre_]); pk = max(post_, key=lambda r: r["interactions"])
    bc = statistics.mean([r["contributors_active"] for r in pre_])
    return {"base_day_int": b, "peak_day_int": pk["interactions"], "peak_x": pk["interactions"] / b, "peak_date": datetime.datetime.fromtimestamp(pk["time"], UTC).strftime("%Y-%m-%d"),
            "base_creators": bc, "peak_creators": max(r["contributors_active"] for r in post_), "sent_pre": statistics.mean([r["sentiment"] for r in pre_ if r.get("sentiment")]), "sent_min_post": min(r["sentiment"] for r in post_ if r.get("sentiment")),
            "days_above_2x": sum(1 for r in post_ if r["interactions"] >= 2 * b), "series": [(datetime.datetime.fromtimestamp(r["time"], UTC).strftime("%m-%d"), r["interactions"], r["sentiment"]) for r in pre_ + post_]}
A["comp"] = {"bybit_feb2025": daily_stats("ts_bybit_feb2025_day", "2025-02-21"), "ftx_nov2022": daily_stats("ts_ftx_nov2022_day", "2022-11-08"), "binance_nov2022": daily_stats("ts_binance_nov2022_day", "2022-11-08"), "binance_nov2023": daily_stats("ts_binance_nov2023_day", "2023-11-21")}
bh = ld("ts_bybit_feb2025_hour")
if bh:
    e0 = int(datetime.datetime(2025, 2, 21, 14, 0, tzinfo=UTC).timestamp())  # Bybit hack ~14:16 UTC Feb 21 2025
    pre_ = [r for r in bh if r["time"] < e0]; post_ = [r for r in bh if r["time"] >= e0][:8]
    b = statistics.mean([r["interactions"] for r in pre_]); bp = statistics.mean([r["posts_created"] for r in pre_]) or 1
    A["comp"]["bybit_hourly"] = {"base_int_h": b, "base_posts_h": bp, "rows": [{"utc": hhmm(r["time"]), "interactions": r["interactions"], "x": r["interactions"] / b, "posts_created": r["posts_created"], "xp": r["posts_created"] / bp, "sentiment": r["sentiment"]} for r in post_]}
# binance 1y daily: rank of yesterday/today, 1y high
b1 = ld("ts_binance_1y_day")
if b1:
    srt = sorted(b1, key=lambda r: -r["interactions"])
    A["binance_1y"] = {"days": len(b1), "top5": [(datetime.datetime.fromtimestamp(r["time"], UTC).strftime("%Y-%m-%d"), r["interactions"], r["contributors_active"]) for r in srt[:5]],
                       "median_day": statistics.median([r["interactions"] for r in b1]), "last3": [(datetime.datetime.fromtimestamp(r["time"], UTC).strftime("%Y-%m-%d"), r["interactions"], r["contributors_active"], r["sentiment"]) for r in b1[-3:]],
                       "series": [(r["time"], r["interactions"]) for r in b1]}

# ---------- 10. Categories: rank among all crypto topics; exchanges dominance; stocks
cc = ld("cat_crypto_interactions") or []
A["cat_crypto_top15"] = [{"title": c["title"], "interactions": c["interactions"], "posts": c["posts_active"], "creators": c["contributors_active"], "sentiment": c.get("sentiment"), "pct24": c.get("percent_change_24h")} for c in cc[:15]]
ex = ld("cat_exchanges") or []
A["exchanges"] = [{"title": c["title"], "interactions": c["interactions"], "posts": c["posts_active"], "creators": c["contributors_active"], "sentiment": c.get("sentiment"), "dominance": c.get("social_dominance")} for c in ex[:12]]
st = ld("cat_stocks_interactions") or []
A["stocks_top"] = [{"title": c["title"], "symbol": c.get("symbol"), "interactions": c["interactions"], "sentiment": c.get("sentiment"), "pct24": c.get("percent_change_24h")} for c in st[:12]]
A["stocks_crypto_names"] = [{"title": c["title"], "symbol": c.get("symbol"), "interactions": c["interactions"], "sentiment": c.get("sentiment"), "pct24": c.get("percent_change_24h")} for c in st if c.get("symbol") in ("COIN", "HOOD", "MSTR", "CRCL", "BMNR", "GLXY", "MARA", "RIOT", "CLSK", "IBIT")]

json.dump(A, open(os.path.join(os.path.dirname(HERE), "analysis.json"), "w"), indent=1, default=str)

# ---------- digest
def k(n):
    n = float(n or 0)
    for d, s in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(n) >= d: return f"{n/d:.1f}{s}" if n/d < 100 else f"{n/d:.0f}{s}"
    return f"{n:.0f}"
out = []
out.append(f"PULLED: {A['meta']['pulled_utc']}  | baseline/h int {k(BASE['interactions'])} posts_created {BASE['posts_created']:.0f} newcreators {BASE['contributors_created']:.0f} sent {BASE['sentiment']:.0f} spam {BASE['spam']:.0f}")
out.append(f"pre-week max hour {k(A['binance_hourly']['pre_max_hour'])}; cum full post hours int {k(A['binance_hourly']['cum_interactions_full_hours'])} posts {A['binance_hourly']['cum_posts_created']} newcreators {A['binance_hourly']['cum_new_contributors']}")
for h in hourly: out.append(f"  {h['utc']} int {k(h['interactions'])} ({h['x_base']:.1f}x base, {h['x_samehour']:.1f}x same-hour) posts {h['posts_created']} ({h['x_posts']:.1f}x) new {h['contributors_created']} active_cr {h['contributors_active']} sent {h['sentiment']} spam {h['spam']}{' PARTIAL' if h['partial'] else ''}")
out.append("NETWORK LAG:")
for n, v in netlag.items(): out.append(f"  {n:10s} base posts/h {v['base_posts_h']:.0f} int/h {k(v['base_int_h'])} | first3x posts {v['first_3x_posts']} int {v['first_3x_int']} | peak posts {v['peak_posts_utc']} {v['peak_posts_x']:.1f}x | post total {v['post_total_full']} int {k(v['int_total_full'])} | sent {v['sent_pre']:.0f}->{v['sent_post']:.0f} | rows " + " ".join(f"{r['utc']}:{r['posts_created']}/{k(r['interactions'])}" for r in v['rows']))
out.append("CONTAGION (peak hour x baseline, 5h):")
for c in A["contagion"]: out.append(f"  {c['display']:24s} peak {c['peak_x']:.1f}x @{c['peak_utc']} ({k(c['peak_int_h'])}/h vs {k(c['base_int_h'])}) posts5h {c['x_posts_5h']:.1f}x newcr {c['x_newcreators_5h']:.1f}x sent {c['sent_pre']:.0f}->{c['sent_post']:.0f} | " + " ".join(f"{h['utc']}:{h['x']:.1f}x/s{h['sentiment']}" for h in c['hours']))
out.append("KEYWORDS:")
for kk, v in kws.items(): out.append(f"  {v['display']:20s} posts {v['posts_prev']}->{v['posts_24h']} creators {v['creators_prev']}->{v['creators_24h']} int {k(v['int_prev'])}->{k(v['int_24h'])} first {v.get('first_utc')} peak {v.get('peak_utc')} {v.get('peak_posts')} | " + " ".join(f"{h['utc'][-5:]}:{h['posts_created']}" for h in v['hourly']))
out.append(f"POSTS loaded {len(PL)} event-window {len(ev)}; classes posts {dict(cl)} int {{{', '.join(f'{a}:{k(b)}' for a,b in cli.items())}}}")
out.append(f"LANG posts {dict(lang.most_common(8))} int {{{', '.join(f'{a}:{k(b)}' for a,b in langi.most_common(8))}}}")
out.append("THEMES: " + " | ".join(f"{t}: {v['posts']}p {k(v['interactions'])} first {v['first_utc']}" for t, v in theme.items()))
out.append("SENT DIST: " + str(A["sentiment_dist"]))
out.append("MINUTE CUM (min: int): " + " ".join(f"{m}:{k(mc[m])}" for m in (5, 10, 15, 20, 30, 45, 60, 90, 120, 180, 240, 299)))
out.append("BREAKERS:")
for b in A["breakers"][:25]: out.append(f"  +{b['min_after']:4d}m {b['utc']} {b['creator']:18s} {k(b['followers']):>6s}f {k(b['interactions']):>6s} {b['cls']:15s} {b['text'][:120]}")
out.append("CREATORS IN WINDOW (top 20):")
for c in A["creators_in_window"][:20]: out.append(f"  {c['name']:18s} {c['cls']:15s} posts {c['posts']} int {k(c['interactions'])} fol {k(c['followers'])} ipf {c['ipf']:.2f} first {c['first_utc']}")
for who in ["cz_binance", "binance", "heyibinance", "richardteng", "elonmusk", "paoloardoino"]:
    if A.get(f"arc_{who}"):
        out.append(f"ARC {who}:"); [out.append(f"  {p['utc']} {k(p['interactions']):>6s} s{p['sentiment']} {p['text'][:140]}") for p in A[f"arc_{who}"]]
out.append("TOP BY NETWORK:")
for n, rows in A["top_by_network"].items():
    out.append(f" {n}:"); [out.append(f"   {r['utc']} {r['creator']} {k(r['interactions'])} s{r['sentiment']} {r['text'][:130]}") for r in rows[:5]]
out.append(f"CONCENTRATION top1 {A['creator_concentration']['top1_share']:.1%} top10 {A['creator_concentration']['top10_share']:.1%}")
out.append("SNAPSHOTS 24h:")
for t, s in snaps.items(): out.append(f"  {s['display']:24s} int {k(s['int_prev'])}->{k(s['int_24h'])} posts {s['posts_prev']}->{s['posts_24h']} creators {s['creators_prev']}->{s['creators_24h']} new {s['newcreators_prev']}->{s['newcreators_24h']} 1yhigh {k(s['int_1y_high'])} netsent {s['net_sent']}")
out.append("COMPARABLES: " + json.dumps({kk: ({a: b for a, b in v.items() if a != 'series'} if v else None) for kk, v in A['comp'].items() if kk != 'bybit_hourly'}, default=str))
if A["comp"].get("bybit_hourly"): out.append("BYBIT HOURLY: base " + k(A['comp']['bybit_hourly']['base_int_h']) + " | " + " ".join(f"{r['utc']}:{r['x']:.1f}x/p{r['xp']:.1f}x/s{r['sentiment']}" for r in A['comp']['bybit_hourly']['rows']))
if A.get("binance_1y"): out.append("BINANCE 1Y: " + json.dumps({a: b for a, b in A['binance_1y'].items() if a != 'series'}))
out.append("CRYPTO TOP15 24h: " + " | ".join(f"{c['title']} {k(c['interactions'])} s{c['sentiment']} {c['pct24']:.1f}%" for c in A['cat_crypto_top15']))
out.append("EXCHANGES: " + " | ".join(f"{c['title']} {k(c['interactions'])} dom{c['dominance']:.1f} s{c['sentiment']}" for c in A['exchanges']))
out.append("STOCKS crypto names: " + " | ".join(f"{c['symbol']} {k(c['interactions'])} s{c['sentiment']} {c['pct24']}" for c in A['stocks_crypto_names']) + " || top: " + " | ".join(f"{c['symbol']} {k(c['interactions'])}" for c in A['stocks_top'][:8]))
open(os.path.join(HERE, "digest.txt"), "w").write("\n".join(out)); print("\n".join(out))

# ---------- 11. Network timing from post samples (the --network flag on time-series is ignored by the API; use post timestamps)
A = json.load(open(os.path.join(os.path.dirname(HERE), "analysis.json")))
nt = {}
STRICT = re.compile(r"hack|exploit|drain|hot wallet|safu|freez|froze|withdraw|stolen|compromis|\$[0-9.]+ ?b|billion|взлом|hackeo|piratage")
for n in ["tweet", "tiktok-video", "youtube-video", "reddit-post", "news", "instagram-post"]:
    rows = sorted([p for p in ev if p["post_type"] == n and p["post_created"] >= EVENT_TS - 120 and STRICT.search(text(p))], key=lambda p: p["post_created"])
    if not rows: nt[n] = {"n": 0}; continue
    firsts = rows[:3]
    byh = Counter(hhmm((p["post_created"] // 3600) * 3600) for p in rows)
    nt[n] = {"n": len(rows), "first_utc": dstr(rows[0]["post_created"]), "first_min_after": round((rows[0]["post_created"] - EVENT_TS) / 60), "first_creator": rows[0].get("creator_name"),
             "median_min_after": round(statistics.median([(p["post_created"] - EVENT_TS) / 60 for p in rows])), "by_hour": dict(byh), "interactions": sum(p.get("interactions_total") or 0 for p in rows),
             "p10_min": round(sorted([(p["post_created"] - EVENT_TS) / 60 for p in rows])[max(0, len(rows) // 10)])}
A["network_timing"] = nt
sn = A["snapshots"]["binance"]
A["network_24h"] = {"posts": sn["net_posts"], "interactions": sn["net_int"], "sentiment": sn["net_sent"]}
# spam share and new-creator share per hour
for h in A["binance_hourly"]["post"]:
    h["spam_share"] = h["spam"] / max(h["posts_active"], 1); h["new_creator_share_of_active"] = h["contributors_created"] / max(h["contributors_active"], 1)
A["binance_hourly"]["baseline"]["spam_share"] = BASE["spam"] / BASE["posts_active"]; A["binance_hourly"]["baseline"]["new_creator_share_of_active"] = BASE["contributors_created"] / BASE["contributors_active"]
json.dump(A, open(os.path.join(os.path.dirname(HERE), "analysis.json"), "w"), indent=1, default=str)
print("NETWORK TIMING:", json.dumps(nt, indent=0)[:3000])
print("SPAM/NEW:", [(h["utc"], round(h["spam_share"], 3), round(h["new_creator_share_of_active"], 2)) for h in A["binance_hourly"]["post"]], "base", round(A["binance_hourly"]["baseline"]["spam_share"], 3), round(A["binance_hourly"]["baseline"]["new_creator_share_of_active"], 3))
