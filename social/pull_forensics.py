import subprocess, os, json, time
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),"raw"); LOG=open(os.path.join(R,"pull.log"),"a")
def run(name,args):
    p=os.path.join(R,name+".json")
    if os.path.exists(p) and os.path.getsize(p)>300: return
    try:
        out=subprocess.run(["lunarcrush"]+args+["--json"],capture_output=True,text=True,timeout=120).stdout; json.loads(out); open(p,"w").write(out); LOG.write(f"ok {name} {len(out)}B\n")
    except Exception as e: LOG.write(f"FAIL {name} {e}\n")
    LOG.flush()
SLEUTHS=["whale_alert","zachxbt","lookonchain","spreekaway","PeckShieldAlert","CyversAlerts","SlowMist_Team","tayvano_","0xngmi","odysseas_eth","samczsun","bwenews","ArkhamIntel","blockaid_","officer_secret","DarkWebInformer","0xfoobar","0xQuit","CertiKAlert","BeosinAlert","AnciliaInc","EmberCN","ai_9684xtpa","TheBlock__","Cointelegraph","WuBlockchain","coinbureau","Spreekaway","hackenclub","dedaub","Mudit__Gupta","pcaversaccio","bantg","evilcos","yihe_binance","binancezh","Binance_Customer","BinanceHelpDesk","ConorGrogan","nikitabier","TreeNewsFeed","DeItaone"]
for c in SLEUTHS:
    run(f"creatorposts_{c}",["creator","twitter",c,"posts","--limit","100"])
for k in ["EIP-7702","7702","Binance 14","hot wallet exploiter","Binance hot wallet","exploiter","delegation","Tornado Cash","binance exploit","binance drained","binance 7702","Ledger supply chain","injection attack","binance withdrawal","binance suspicious","binance wallet"]:
    n=k.replace(" ","_").replace("-","")
    run(f"kwposts_{n}",["keyword",k,"posts","--limit","200"])
    run(f"kw_{n}",["keyword",k])
run("posts_binance_1d_1000",["topic","binance","posts","--interval","1d","--limit","1000"])
run("posts_binance_1w_1000",["topic","binance","posts","--interval","1w","--limit","1000"])
for t in ["tornado","ledger","ethereum","tether","usdc","aave","bnb","bitcoin"]:
    run(f"posts_{t}_1d_500",["topic",t,"posts","--interval","1d","--limit","500"])
LOG.write("FORENSICS DONE\n"); print("done")
