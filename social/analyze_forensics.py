#!/usr/bin/env python3
"""Read every post pulled and build the forensic ledger: pre-event signals, on-chain claims by minute, mechanism hypotheses, sleuth activity, Whale Alert ledger."""
import json,glob,re,datetime,os
from collections import Counter,defaultdict
HERE=os.path.dirname(os.path.abspath(__file__)); R=os.path.join(HERE,"raw"); UTC=datetime.UTC
EV=1793305440; T0=1793304000; DAY0=1793145600  # Oct 28 00:00
posts={}
for f in glob.glob(os.path.join(R,"posts_*.json"))+glob.glob(os.path.join(R,"kwposts_*.json"))+glob.glob(os.path.join(R,"creatorposts_*.json")):
    if f.endswith(("jul12.json","mar18.json")): continue
    try: d=json.load(open(f)); d=d.get("data",d)
    except Exception: continue
    for p in d or []:
        if p.get("post_created"): posts[(p["post_type"],p["id"])]=p
P=sorted(posts.values(),key=lambda p:p["post_created"])
def T(p): return datetime.datetime.fromtimestamp(p["post_created"],UTC).strftime("%m-%d %H:%M")
def txt(p): return ((p.get("post_title") or "")+" "+(p.get("post_description") or "")+" "+(p.get("post_extraText") or ""))
def low(p): return txt(p).lower()
def eng(p): return p.get("interactions_total") or 0
W=[p for p in P if DAY0<=p["post_created"]<1793325600]
print("unique posts",len(P),"Oct28-Oct30 01:30:",len(W))
A={}
# ---- 1. pre-event: Oct 28 00:00 -> Oct 29 20:24, security-themed and Binance-themed
SEC=re.compile(r"ledger|supply chain|injection|front.?end|phish|drainer|7702|delegat|private key|seed phrase|compromis|exploit|hack|malicious|revoke|approval",re.I)
BIN=re.compile(r"binance|cz_binance|\bcz\b|\bbnb\b|heyibinance|richardteng",re.I)
pre=[p for p in W if p["post_created"]<EV]
pre_sec=[p for p in pre if SEC.search(txt(p))]
pre_bin_sec=[p for p in pre_sec if BIN.search(txt(p))]
A["pre_event"]={"n_posts":len(pre),"n_security":len(pre_sec),"n_binance_security":len(pre_bin_sec),
 "top_security":[{"utc":T(p),"creator":p.get("creator_name"),"followers":p.get("creator_followers"),"eng":eng(p),"text":txt(p)[:260].replace("\n"," ")} for p in sorted(pre_sec,key=lambda p:-eng(p))[:40]],
 "binance_security":[{"utc":T(p),"creator":p.get("creator_name"),"eng":eng(p),"text":txt(p)[:260].replace("\n"," ")} for p in sorted(pre_bin_sec,key=lambda p:-eng(p))[:30]]}
# themes of the day before the event
DAYTH=[("Ledger supply chain / hardware",r"ledger"),("Polymarket front-end injection",r"polymarket"),("front-end / injection attack",r"inject|front.?end"),("phishing / drainer",r"phish|drainer"),("EIP-7702 / delegation",r"7702|delegat"),("Binance withdrawals / wallet ops",r"binance.{0,60}(withdraw|maintenance|wallet)|(withdraw|maintenance|wallet).{0,60}binance")]
A["pre_event"]["themes"]={t:{"posts":sum(1 for p in pre if re.search(rx,low(p))),"eng":sum(eng(p) for p in pre if re.search(rx,low(p))),"first":next((T(p)+" "+(p.get("creator_name") or "") for p in pre if re.search(rx,low(p))),None)} for t,rx in DAYTH}
# ---- 2. on-chain claim ledger: first mention of each fact
ev=[p for p in W if p["post_created"]>=EV-600]
FACTS=[("Binance 14 wallet named",r"binance ?14\b"),("Binance 16 named",r"binance ?16\b"),("EIP-7702 / delegation named",r"7702|delegat"),("Tornado Cash funding",r"tornado"),("contract pre-deployed / prepared",r"deploy|pre-?deploy|prepared|planned"),("50 delegations / nonces",r"50 delegations|fifty|nonce"),("private key compromised",r"private key|key (was|has been|got) (stolen|compromised|leaked)|compromised key|key compromise"),("signing system / Safe-style (Bybit-like)",r"signing|signer|multisig|safe\{?wallet|bybit"),("insider / inside job",r"insider|inside job"),("internal migration / maintenance (benign read)",r"migration|maintenance|internal transfer|consolidat"),("XRP outflow",r"\bxrp\b.{0,80}(binance|unknown|wallet)|binance.{0,80}\bxrp\b"),("SOL outflow",r"\bsol\b.{0,80}(binance|unknown|wallet)|binance.{0,80}\bsol\b"),("Bitcoin outflow",r"\bbtc\b|bitcoin"),("Tron / USDT TRC20 outflow",r"\btron\b|\btrx\b|trc-?20"),("Arbitrum/Base/Optimism outflow",r"arbitrum|\bbase\b|optimism"),("Tether freeze",r"tether.{0,40}(froze|freez)|(froze|freez).{0,40}usdt"),("Circle freeze",r"circle.{0,40}(froze|freez)|(froze|freez).{0,40}usdc"),("Ripple / RLUSD freeze",r"ripple|rlusd"),("WLFI / USD1 freeze",r"wlfi|usd1|world liberty"),("Aave borrow by attacker",r"aave"),("swapping stables to ETH",r"swap|convert|dump"),("ETH cannot be frozen",r"eth (can'?t|cannot) be frozen|can'?t freeze eth|unfreez"),("revocation of delegation",r"revok"),("Etherscan 'Exploiter' label",r"exploiter"),("Lazarus / DPRK speculation",r"lazarus|north korea|dprk"),("Binance.US unaffected",r"binance\.?us"),("test run / earlier wallets",r"test run|dry run|rehears|smaller wallets|earlier in the day"),("Hot Wallet 34",r"hot wallet 34"),("Polymarket same day",r"polymarket"),("Ledger same day",r"ledger")]
ledger=[]
for name,rx in FACTS:
    rxc=re.compile(rx,re.I); hits=[p for p in ev if rxc.search(txt(p))]
    if not hits: ledger.append({"fact":name,"n":0}); continue
    first=hits[0]; top=max(hits,key=eng)
    ledger.append({"fact":name,"n":len(hits),"eng":sum(eng(p) for p in hits),"first_utc":T(first),"first_min":round((first["post_created"]-EV)/60),"first_creator":first.get("creator_name"),"first_followers":first.get("creator_followers"),"first_eng":eng(first),"first_text":txt(first)[:220].replace("\n"," "),"top_creator":top.get("creator_name"),"top_eng":eng(top),"top_utc":T(top),"top_text":txt(top)[:200].replace("\n"," ")})
A["claim_ledger"]=ledger
# ---- 3. mechanism hypotheses share
HYP=[("EIP-7702 delegation abuse (what happened on-chain)",r"7702|delegat"),("Private key theft",r"private key|stolen key|key (was|has been) (stolen|compromised|leaked)|compromised key"),("Signing infrastructure / front-end manipulation (Bybit-style)",r"signing (system|infra)|signer|front.?end|safe wallet|safe\{|like bybit|bybit-style|supply chain|inject"),("Insider",r"insider|inside job"),("Benign: internal migration / maintenance",r"migration|maintenance|internal transfer|just fud|it'?s fud"),("State-actor speculation",r"lazarus|north korea|dprk|state.actor")]
A["hypotheses"]=[{"hypothesis":h,"posts":sum(1 for p in ev if re.search(rx,low(p))),"eng":sum(eng(p) for p in ev if re.search(rx,low(p))),"first":next((T(p)+" @"+(p.get("creator_name") or "") for p in ev if re.search(rx,low(p))),None)} for h,rx in HYP]
# ---- 4. sleuth accounts
SL=["spreekaway","zachxbt","lookonchain","PeckShieldAlert","CyversAlerts","SlowMist_Team","tayvano_","0xngmi","odysseas_eth","samczsun","bwenews","ArkhamIntel","blockaid_","officer_secret","DarkWebInformer","0xfoobar","0xQuit","CertiKAlert","BeosinAlert","AnciliaInc","EmberCN","ai_9684xtpa","WuBlockchain","hackenclub","dedaub","Mudit__Gupta","pcaversaccio","bantg","evilcos","ConorGrogan","TreeNewsFeed","whale_alert","DeItaone","StarPlatinum_","KillaXBT"]
sl={}
for s in SL:
    rows=[p for p in ev if (p.get("creator_name") or "").lower()==s.lower()]
    if not rows: continue
    sl[s]={"posts":len(rows),"eng":sum(eng(p) for p in rows),"followers":rows[0].get("creator_followers"),"first_utc":T(rows[0]),"first_min":round((rows[0]["post_created"]-EV)/60),"first_text":txt(rows[0])[:200].replace("\n"," "),"top_text":txt(max(rows,key=eng))[:200].replace("\n"," "),"top_eng":eng(max(rows,key=eng))}
A["sleuths"]=dict(sorted(sl.items(),key=lambda kv:kv[1]["first_min"]))
# ---- 5. Whale Alert ledger (all posts Oct 29 15:00 -> 01:30)
wa=[p for p in P if (p.get("creator_name") or "").lower()=="whale_alert" and 1793286000<=p["post_created"]<1793325600]
def parse(p):
    t=txt(p).replace("\n"," "); m=re.search(r"([\d,\.]+)\s*\$?([A-Z]{2,6})\s*\(([\d,\.]+) USD\)\s*(transferred from|minted at|has just been frozen)?\s*(.*?)(?:$|\s{2,})",t)
    return {"utc":T(p),"eng":eng(p),"amount":m.group(1) if m else None,"asset":m.group(2) if m else None,"usd":m.group(3) if m else None,"what":t[:160]}
A["whale_alert"]=[parse(p) for p in sorted(wa,key=lambda p:p["post_created"])]
A["whale_alert_summary"]={"n":len(wa),"from_binance_pre_2024":[w for w in A["whale_alert"] if "from #Binance" in w["what"] and w["utc"]<"10-29 20:24"],"frozen":[w for w in A["whale_alert"] if "frozen" in w["what"]]}
# ---- 6. hour-by-hour sleuth vs aggregator vs official first-mention race for key facts already computed; plus 'fud' vs 'hack' in first 30 min
f30=[p for p in ev if EV<=p["post_created"]<EV+1800]
A["first30"]={"posts":len(f30),"hack_framed":sum(1 for p in f30 if re.search(r"hack|exploit|drain",low(p))),"fud_framed":sum(1 for p in f30 if re.search(r"fud|migration|maintenance|nothing|calm",low(p))),"eng_hack":sum(eng(p) for p in f30 if re.search(r"hack|exploit|drain",low(p))),"eng_fud":sum(eng(p) for p in f30 if re.search(r"fud|migration|maintenance",low(p)))}
json.dump(A,open(os.path.join(HERE,"analysis_forensics.json"),"w"),indent=1)
# digest
o=[]
o.append(f"PRE-EVENT (Oct 28 00:00 -> Oct 29 20:24): posts {A['pre_event']['n_posts']} security-themed {A['pre_event']['n_security']} binance+security {A['pre_event']['n_binance_security']}")
for t,v in A["pre_event"]["themes"].items(): o.append(f"  theme {t}: {v}")
o.append("  TOP SECURITY POSTS BEFORE 20:24:"); [o.append(f"   {x['utc']} @{x['creator']} {x['eng']} | {x['text'][:170]}") for x in A["pre_event"]["top_security"][:25]]
o.append("  BINANCE+SECURITY BEFORE 20:24:"); [o.append(f"   {x['utc']} @{x['creator']} {x['eng']} | {x['text'][:170]}") for x in A["pre_event"]["binance_security"][:15]]
o.append("CLAIM LEDGER (first mention):")
for l in ledger:
    if l["n"]: o.append(f"  {l['fact']:45s} n={l['n']:4d} eng={l['eng']/1e6:5.1f}M first +{l['first_min']:4d}m {l['first_utc']} @{l['first_creator']} ({l['first_followers']}f, {l['first_eng']}) | {l['first_text'][:120]} || top @{l['top_creator']} {l['top_eng']} {l['top_utc']}")
    else: o.append(f"  {l['fact']:45s} n=0")
o.append("HYPOTHESES:"); [o.append(f"  {h}") for h in A["hypotheses"]]
o.append("SLEUTHS (by first post):"); [o.append(f"  {k:18s} +{v['first_min']:4d}m {v['first_utc']} posts {v['posts']} eng {v['eng']/1e3:.0f}K fol {v['followers']} | first: {v['first_text'][:110]} || top({v['top_eng']}): {v['top_text'][:90]}") for k,v in A["sleuths"].items()]
o.append("WHALE ALERT LEDGER:"); [o.append(f"  {w['utc']} {w['eng']:>7} {w['what'][:140]}") for w in A["whale_alert"]]
o.append(f"FIRST 30 MIN: {A['first30']}")
open(os.path.join(HERE,"digest_forensics.txt"),"w").write("\n".join(o)); print("\n".join(o))
