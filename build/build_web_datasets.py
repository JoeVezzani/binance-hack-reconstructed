#!/usr/bin/env python3
"""Downloadable datasets (CSV + Parquet) and the AI guide for the web study. Run with a Python that has pyarrow.
Reads web/events.json (written by build_web_assets.py), part1.json, analysis.json and the live re-verification."""
import os, json, csv
import pyarrow as pa, pyarrow.parquet as pq
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SLUG = "binance-hack-reconstructed"; OUT = os.path.join(ROOT, "web", SLUG)
P1 = json.load(open(os.path.join(ROOT, "part1.json"))); A = json.load(open(os.path.join(ROOT, "analysis.json")))
POS = json.load(open(os.path.join(ROOT, "onchain", "reverify_20261030T032016Z", "positions.json")))
EV = json.load(open(os.path.join(ROOT, "web", "events.json")))
LANE = {"fund": "Funding", "prep": "Build and rehearse", "attack": "Attacker on Binance 14", "issuer": "Issuer freezes", "binance": "Binance", "social": "Social", "other": "Other chains", "market": "Market"}
def iso(d, t): return f"2026-10-{d}T{t if t.count(':') == 2 else t + ':00'}Z"

def write(name, cols, rows):
    with open(os.path.join(OUT, name + ".csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(cols); w.writerows(rows)
    tbl = pa.table({c: [r[i] for r in rows] for i, c in enumerate(cols)})
    pq.write_table(tbl, os.path.join(OUT, name + ".parquet"), compression="zstd")
    return len(rows)

n = {}
n["events"] = write("lc_binance_hack_events", ["time_utc", "end_utc", "lane", "event", "detail", "first_public"],
    sorted([[iso(e["day"], e["time"]), iso(*e["end"]) if e["end"] else None, LANE[e["lane"]], e["title"], e["detail"], e["first_public"] or None] for e in EV], key=lambda r: r[0]))
rows = []
for a in P1["acts"]:
    for s in a.get("steps", []): rows.append([f'{a["n"]}', a["title"], s["t"], s["title"], s["body"], s.get("seen") or None])
n["timeline"] = write("lc_binance_hack_timeline", ["act", "act_title", "time_utc", "step", "detail", "first_public"], rows)
_aave = [f for f in POS["frozen"] if "Aave" in f["asset"]]
for f in _aave: POS["frozen"].remove(f); POS["held"].append({**f, "usd": 16.3, "chain": f.get("chain") or "Ethereum", "asset": "aUSDT (Aave), net of debt", "status": "Collateral net of WETH debt; withdrawable within health-factor limits"})
rows = [[r["chain"], r["asset"], float(r["amount"]) if r.get("amount") not in (None, "") else None, float(r["usd"]), r["where"], "unfrozen", r["status"], r.get("read_utc")] for r in POS["held"]]
rows += [[r.get("chain"), r["asset"], float(r["amount"]) if r.get("amount") not in (None, "") else None, float(r["usd"]), r["where"], "frozen, recovered or immobilised", r.get("how"), r.get("read_utc")] for r in POS["frozen"]]
n["positions"] = write("lc_binance_hack_positions", ["chain", "asset", "amount", "usd_millions", "address", "status", "detail", "read_utc"], rows)
CLS = {"official": "official", "news_aggregator": "news aggregator", "large": "large account", "mid": "mid-size account", "small": "small account"}
rows = [[f'2026-10-{p["utc"][4:6]}T{p["utc"][-5:]}:00Z', p["creator"], p["type"].replace("-video", "").replace("-post", "").replace("tweet", "x"), int(float(p["followers"])),
         int(float(p["interactions"])), float(p["sentiment"]), CLS.get(p.get("cls"), p.get("cls")), p.get("link"), " ".join(p["text"].split())]
        for p in A["top_posts"] if p["creator"] != "LizardX"]
n["posts"] = write("lc_binance_hack_top_posts", ["time_utc", "account", "network", "followers", "engagements", "post_sentiment_1_to_5", "account_class", "url", "text"], rows)
for f in ("lc_binance_hack_positions.csv", "lc_binance_hack_timeline.csv"): pass

guide = f"""# The Binance Hack, Reconstructed: guide for AI assistants and analysts

LunarCrush Research, October 2026. Page: https://lunarcrush.com/research/{SLUG}
Full report (80 pages): LunarCrush-Binance-Hack-Reconstructed.pdf

## What this is
A step-by-step reconstruction of the October 29, 2026 Binance hot-wallet hack, built from the Ethereum record, live balance reads on six chains, and LunarCrush social data (X, TikTok, YouTube, Instagram, Reddit and news).

## Key facts (UTC)
- Operator funded through Tornado Cash from Oct 28 07:39 (about 1.49 ETH in total). Sweeper v1 deployed Oct 29 02:28:59. Rehearsals at 13:51 and 16:20 on the operator's own wallets.
- 20:20:59: one transaction delivered 50 EIP-7702 authorizations signed by Binance 14's key; exactly one applied (nonce 18914809).
- 20:24:23: one sweep moved 167,464 ETH and 63 tokens for about $0.93 in gas. Attacker code stayed on Binance 14 until 00:10:35 (3h 49m).
- Binance said at 00:13 it would cover all losses and at 00:52 that about $3B was frozen.
- Live re-read 03:20 to 03:27 UTC Oct 30: about $2.66B frozen or recovered; about $2.83B unfrozen in traced addresses (including $16.3M of Aave collateral net of debt).

## Files (each as .csv and .parquet)
- lc_binance_hack_events: {n['events']} rows. Every event on the page's interactive timelines. Columns: time_utc, end_utc (spans only), lane, event, detail, first_public.
- lc_binance_hack_timeline: {n['timeline']} rows. The step-by-step acts. Columns: act, act_title, time_utc, step, detail, first_public.
- lc_binance_hack_positions: {n['positions']} rows. Every traced balance, read live. Columns: chain, asset, amount, usd_millions, address, status, detail, read_utc.
- lc_binance_hack_top_posts: {n['posts']} rows. The most-engaged sampled posts from 20:14 UTC Oct 29 to 01:00 UTC Oct 30. Columns: time_utc, account, network, followers, engagements, post_sentiment_1_to_5 (3 = neutral), account_class, url, text.

## How it was built
- Ethereum: transactions, receipts, contract code and the 50 authorizations decoded from a public JSON-RPC node; address histories and token transfers from the Blockscout API.
- Balances: read live 03:20 to 03:27 UTC Oct 30 on Ethereum, Bitcoin (mempool.space), Tron (TronGrid), XRP Ledger (s1.ripple.com), Solana and Arbitrum. Freeze status read from each token contract. Prices: CoinGecko, 03:22 UTC.
- Social: LunarCrush topic, keyword and post data pulled 01:00 to 01:30 UTC Oct 30. Each on-chain step is matched to the first public post that described it.
- Attribution of the Bitcoin, Tron, XRP and Solana senders to Binance comes from Whale Alert labels.

## Rules for quoting
Attribute loss figures to their source; Binance has not confirmed a loss total. Do not name an attacker. USD values are as of the read time above.
"""
open(os.path.join(OUT, "lc_binance_hack_ai_guide.md"), "w").write(guide)
for fn in sorted(os.listdir(OUT)): print(f"{os.path.getsize(os.path.join(OUT, fn)) / 1024:8.0f} KB  {fn}")
