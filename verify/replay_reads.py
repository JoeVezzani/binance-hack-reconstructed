#!/usr/bin/env python3
"""Replay every on-chain read behind Act V and compare it with what we recorded.

Each file in onchain/reverify_20261030T032016Z/ holds the exact request we sent (URL, JSON-RPC body or GET),
the UTC time we sent it and the response we got (03:20 to 03:27 UTC, Oct 30 2026). This script sends the same
requests again to the same public, keyless endpoints and reports, per file, whether the answer still matches.

Balances move and explorers paginate, so "changed" is expected for some reads; "error" usually means a
public endpoint is rate-limiting you (re-run with --sleep 1).

Standard library only.  Usage:
    python3 verify/replay_reads.py                 # everything (about 220 requests)
    python3 verify/replay_reads.py --only eth_ btc_addr   # filename prefixes
"""
import argparse, glob, json, os, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(os.path.dirname(HERE), "onchain", "reverify_20261030T032016Z")
SKIP = {"_read_log.json", "positions.json", "synthesis_patch.json", "btc_tree_summary.json"}


def send(url, req, timeout=30):
    headers = {"User-Agent": "lc-binance-hack-replay/1.0", "Accept": "application/json"}
    if isinstance(req, dict):
        data = json.dumps(req).encode()
        headers["Content-Type"] = "application/json"
        r = urllib.request.Request(url, data=data, headers=headers, method="POST")
    else:
        r = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def core(x):
    """The part worth comparing: JSON-RPC result if present, else the whole body."""
    return x.get("result", x) if isinstance(x, dict) else x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=[], help="filename prefixes to replay")
    ap.add_argument("--sleep", type=float, default=0.25)
    a = ap.parse_args()
    files = sorted(f for f in glob.glob(os.path.join(DIR, "*.json")) if os.path.basename(f) not in SKIP)
    if a.only: files = [f for f in files if os.path.basename(f).startswith(tuple(a.only))]
    tally = {"same": 0, "changed": 0, "error": 0}
    for f in files:
        rec = json.load(open(f))
        if not isinstance(rec, dict) or "url" not in rec or "response" not in rec: continue
        name = os.path.basename(f)[:-5]
        try:
            now = send(rec["url"], rec.get("request"))
            same = core(now) == core(rec["response"])
            tally["same" if same else "changed"] += 1
            if not same:
                was, new = json.dumps(core(rec["response"]))[:90], json.dumps(core(now))[:90]
                print(f"changed  {name}\n         recorded {rec['utc']}: {was}\n         now: {new}")
        except Exception as e:  # rate limits, endpoint changes
            tally["error"] += 1
            print(f"error    {name}: {e}")
        time.sleep(a.sleep)
    print(f"\n{tally['same']} identical, {tally['changed']} changed, {tally['error']} errors (of {sum(tally.values())} replayed)")


if __name__ == "__main__":
    sys.exit(main())
