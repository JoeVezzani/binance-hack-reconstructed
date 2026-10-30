#!/usr/bin/env python3
"""Pull everything for the Binance hack report from the LunarCrush CLI into raw/. Idempotent: skips files that exist and are non-trivial."""
import subprocess, os, json, sys, time
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw"); os.makedirs(R, exist_ok=True)
LOG = open(os.path.join(R, "pull.log"), "a")
def run(name, args):
    p = os.path.join(R, name + ".json")
    if os.path.exists(p) and os.path.getsize(p) > 300: return
    t = time.time()
    try:
        out = subprocess.run(["lunarcrush"] + args + ["--json"], capture_output=True, text=True, timeout=120).stdout
        json.loads(out); open(p, "w").write(out); LOG.write(f"ok {name} {len(out)}B {time.time()-t:.1f}s\n")
    except Exception as e:
        LOG.write(f"FAIL {name} {args} {e}\n")
    LOG.flush()
TOPICS = ["binance","bnb","bitcoin","ethereum","tether","usdc","hyperliquid","coinbase","okx","bybit","kraken","solana","xrp","tornado","crypto","$coin","$hood","$mstr","gold"]
for t in TOPICS:
    run(f"topic_{t.strip('$')}", ["topic", t])
    run(f"ts_{t.strip('$')}_1w_hour", ["topic", t, "time-series", "--interval", "1w", "--bucket", "hour"])
for t in ["binance","bnb","bitcoin","ethereum","hyperliquid","coinbase","bybit","tether"]:
    run(f"ts_{t}_1y_day", ["topic", t, "time-series", "--interval", "1y", "--bucket", "day"])
# comparables: Bybit hack Feb 21 2025, FTX Nov 2022
run("ts_bybit_feb2025_day", ["topic", "bybit", "time-series", "--start", "2025-02-01", "--end", "2025-03-20", "--bucket", "day"])
run("ts_bybit_feb2025_hour", ["topic", "bybit", "time-series", "--start", "2025-02-19", "--end", "2025-02-25", "--bucket", "hour"])
run("ts_ftx_nov2022_day", ["topic", "ftx", "time-series", "--start", "2022-10-25", "--end", "2022-12-10", "--bucket", "day"])
run("ts_binance_nov2022_day", ["topic", "binance", "time-series", "--start", "2022-10-25", "--end", "2022-12-10", "--bucket", "day"])
run("ts_binance_nov2023_day", ["topic", "binance", "time-series", "--start", "2023-11-01", "--end", "2023-12-15", "--bucket", "day"])  # CZ plea / DOJ settlement Nov 21 2023
# per-network hourly for binance
for n in ["twitter","tiktok","youtube","reddit","instagram","news"]:
    run(f"ts_binance_1w_hour_{n}", ["topic", "binance", "time-series", "--interval", "1w", "--bucket", "hour", "--network", n])
# keywords
KW = ["binance hack","binance hacked","SAFU","cz","user funds are safe","binance withdrawals","hot wallet","EIP-7702","tether freeze","crypto hack","not your keys","largest hack","bank run","bybit hack","lazarus","north korea","withdraw","binance down"]
for k in KW:
    n = k.replace(" ", "_").replace("-", "")
    run(f"kw_{n}", ["keyword", k])
    run(f"kwts_{n}_1w_hour", ["keyword", k, "time-series", "--interval", "1w", "--bucket", "hour"])
for k in ["binance hack","SAFU","not your keys","lazarus","withdraw"]:
    n = k.replace(" ", "_")
    run(f"kwposts_{n}", ["keyword", k, "posts", "--limit", "200"])
# posts
run("posts_binance_1000", ["topic", "binance", "posts", "--limit", "1000"])
for n in ["tiktok","youtube","reddit","news","instagram"]:
    run(f"posts_binance_{n}", ["topic", "binance", "posts", "--limit", "100", "--network", n])
for t in ["bnb","bitcoin","ethereum","tether","hyperliquid","coinbase","cz"]:
    run(f"posts_{t}_200", ["topic", t, "posts", "--limit", "200"])
# creators
for t in ["binance","bnb","bitcoin","ethereum"]:
    run(f"creators_{t}", ["creators", t, "--limit", "100"])
for c in ["cz_binance","binance","WatcherGuru","KobeissiLetter","lookonchain","zachxbt","PeckShieldAlert","whale_alert","Cointelegraph","CoinDesk","heyibinance","richardteng","elonmusk"]:
    run(f"creator_{c}", ["creator", "twitter", c])
    run(f"creatorposts_{c}", ["creator", "twitter", c, "posts", "--limit", "50"])
# categories
run("cat_crypto_interactions", ["category", "cryptocurrencies", "--sort", "interactions", "--limit", "100"])
run("cat_crypto_altrank", ["category", "cryptocurrencies", "--sort", "alt_rank", "--limit", "50"])
run("cat_stocks_interactions", ["category", "stocks", "--sort", "interactions", "--limit", "50"])
run("cat_exchanges", ["category", "exchanges"])
run("categories", ["categories"])
LOG.write("DONE\n"); print("done")
