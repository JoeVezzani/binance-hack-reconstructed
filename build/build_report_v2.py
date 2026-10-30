#!/usr/bin/env python3
"""v2 PDF: The Binance Hack, Reconstructed (additive; v1 builder untouched).
Inputs: part1.json, chapters_v2/*.json (fallback chapters/*.json), chapters/flow_verified.json (Act V, only if present),
synthesis.json (v1 night/timeline/about), analysis.json, build/charts/*.png."""
import json, os, re, html
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); CHD = os.path.join(HERE, "charts")
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether,
                                NextPageTemplate, CondPageBreak, Flowable)
from reportlab.lib.styles import ParagraphStyle

F = os.path.join(HERE, "fonts")
def _first(*names):
    for nm in names:
        if os.path.exists(os.path.join(F, nm)): return os.path.join(F, nm)
    return os.path.join(F, "PlusJakartaSans-400.ttf")
# Plus Jakarta Sans (OFL) ships in build/fonts. Butler and Input Mono are not redistributed: drop them into
# build/fonts to match the published PDF exactly; otherwise JetBrains Mono / Plus Jakarta Sans stand in.
for n, path in (("PJS", _first("PlusJakartaSans-400.ttf")), ("PJS-M", _first("PlusJakartaSans-500.ttf")), ("PJS-SB", _first("PlusJakartaSans-600.ttf")),
                ("PJS-B", _first("PlusJakartaSans-700.ttf")), ("PJS-XB", _first("PlusJakartaSans-800.ttf")), ("Butler", _first("Butler-Light.ttf", "PlusJakartaSans-400.ttf")),
                ("Mono", _first("InputMono-Light.ttf", "JetBrainsMono-Light.ttf", "JetBrainsMono-Regular.ttf")), ("Mono-M", _first("InputMono-Medium.ttf", "JetBrainsMono-Medium.ttf", "JetBrainsMono-Regular.ttf"))):
    pdfmetrics.registerFont(TTFont(n, path))
pdfmetrics.registerFontFamily("PJS", normal="PJS", bold="PJS-B", italic="PJS", boldItalic="PJS-B")

# ---------------------------------------------------------------- palette + type scale
CANVAS, CARD, CARD2 = HexColor("#0B121E"), HexColor("#0E1625"), HexColor("#111C2D")
GREEN, BLUE, AMBER, RED, VIOLET = HexColor("#14B881"), HexColor("#6EA6F8"), HexColor("#F2A93B"), HexColor("#FF7A7A"), HexColor("#B794F6")
ACT = {"blue": BLUE, "red": RED, "green": GREEN, "violet": VIOLET, "amber": AMBER}
WHITE, INK, BODY, MUTED = HexColor("#FFFFFF"), HexColor("#E3E6EE"), HexColor("#B4B9C8"), HexColor("#6E7690")
LINE = Color(1, 1, 1, 0.07); LINE2 = Color(1, 1, 1, 0.13)
def tint(c, a): return Color(c.red, c.green, c.blue, a)
W, H = letter; M = 0.75 * inch; CW = W - 2 * M
def S(name, **kw):
    base = dict(fontName="PJS", fontSize=9.7, leading=15.2, textColor=BODY, spaceAfter=0); base.update(kw); return ParagraphStyle(name, **base)
ST = {"body": S("body", spaceAfter=9), "leads": S("leads", fontSize=11.4, leading=17, textColor=INK, spaceAfter=12), "fbody": S("fbody", fontSize=9.3, leading=14, textColor=BODY, spaceAfter=8), "lead": S("lead", fontSize=12.4, leading=18.6, textColor=INK, spaceAfter=14),
      "h1": S("h1", fontName="Butler", fontSize=36, leading=40, textColor=WHITE, spaceAfter=12), "h1s": S("h1s", fontName="Butler", fontSize=28, leading=32, textColor=WHITE, spaceAfter=12), "h2": S("h2", fontName="Butler", fontSize=24, leading=28, textColor=WHITE, spaceAfter=10),
      "h3": S("h3", fontName="PJS-SB", fontSize=11.6, leading=15.6, textColor=WHITE, spaceAfter=4), "headline": S("headline", fontName="PJS-SB", fontSize=15, leading=20.5, textColor=WHITE, spaceAfter=10),
      "small": S("small", fontSize=7.8, leading=11.2, textColor=MUTED), "smallw": S("smallw", fontSize=8.6, leading=12.6, textColor=BODY, spaceAfter=5),
      "cell": S("cell", fontSize=7.8, leading=10.8, textColor=BODY), "cellw": S("cellw", fontName="PJS-SB", fontSize=7.8, leading=10.8, textColor=WHITE),
      "cellh": S("cellh", fontName="PJS-B", fontSize=6.6, leading=9, textColor=MUTED), "acell": S("acell", fontSize=6.9, leading=9.0, textColor=BODY),
      "acellw": S("acellw", fontName="PJS-SB", fontSize=6.9, leading=9.0, textColor=WHITE),
      "num": S("num", fontName="PJS-XB", fontSize=22, leading=25, textColor=GREEN), "numlab": S("numlab", fontSize=7.9, leading=10.8, textColor=BODY),
      "cardt": S("cardt", fontName="PJS-SB", fontSize=10.2, leading=13.6, textColor=WHITE, spaceAfter=3), "cardb": S("cardb", fontSize=8.6, leading=12.4, textColor=BODY),
      "caption": S("caption", fontSize=7.5, leading=10.6, textColor=MUTED, spaceBefore=4, spaceAfter=12), "toc": S("toc", fontName="PJS-M", fontSize=8.8, leading=11, textColor=INK), "tocd": S("tocd", fontSize=7.3, leading=9.6, textColor=MUTED),
      "quote": S("quote", fontSize=8.8, leading=12.8, textColor=INK), "quotem": S("quotem", fontName="PJS-B", fontSize=7.1, leading=10, textColor=BLUE),
      "steptime": S("steptime", fontName="Mono-M", fontSize=8.4, leading=11, textColor=WHITE), "steptitle": S("steptitle", fontName="PJS-SB", fontSize=10.4, leading=13.8, textColor=WHITE, spaceAfter=2),
      "stepbody": S("stepbody", fontSize=8.8, leading=13.0, textColor=BODY), "seenlab": S("seenlab", fontName="PJS-B", fontSize=6.2, leading=8.5, textColor=MUTED),
      "seen": S("seen", fontName="PJS-M", fontSize=7.9, leading=10.8, textColor=VIOLET),
      "coversub": S("coversub", fontSize=12.6, leading=19, textColor=HexColor("#CDD2DE")), "coverlab": S("coverlab", fontSize=7.6, leading=10.2, textColor=BODY)}

from reportlab.pdfbase.ttfonts import TTFont as _TT
_CMAP = set(_TT("_c", os.path.join(F, "PlusJakartaSans-400.ttf")).face.charToGlyph.keys())
TRANSL = {"币安被盗的是热钱包，损失不会很大的": "What was stolen from Binance is a hot wallet; the losses won't be large. [translated from Chinese]",
          "ИЗ БИРЖИ УШЛО БОЛЬШЕ 3 МИЛЛИАРДОВ": "MORE THAN 3 BILLION HAS LEFT THE EXCHANGE [translated from Russian]"}
def clean(s):
    s = str(s)
    for k, v in TRANSL.items(): s = s.replace(k, v)
    if re.search(r"[\u0600-\u06FF]", s): return "[Arabic-language post on the hack and the $5.7B outflow figure]"
    out = "".join(c for c in s if ord(c) < 128 or ord(c) in _CMAP or c in "…“”‘’·")
    out = re.sub(r"\[\s*\]\s*", "", out); out = re.sub(r"  +", " ", out).strip()
    return out if (out or not s.strip()) else "(emoji reply)"
HEX = re.compile(r"(0x[0-9A-Fa-f]{3,}(?:…[0-9A-Fa-f]{0,8})?)")
def esc(s, ms=8.2):
    s = html.escape(clean(s), quote=False).replace("—", ", ").replace("–", "-")
    return HEX.sub(r'<font name="Mono" size="%s">\1</font>' % ms, s)
def P(t, st="body"): return Paragraph(t, ST[st])

class Kicker(Flowable):
    """Tracked all-caps label (Paragraph cannot letter-space)."""
    def __init__(self, text, color=BLUE, size=7.3, space=1.15, after=7):
        super().__init__(); self.t = text.upper(); self.c = color; self.s = size; self.sp = space; self.after = after
    def wrap(self, aw, ah): return (aw, self.s + self.after)
    def draw(self):
        c = self.canv; c.saveState(); c.setFillColor(self.c); t = c.beginText(0, self.after); t.setFont("PJS-B", self.s); t.setCharSpace(self.sp); t.textLine(self.t); c.drawText(t); c.restoreState()
def K(text, color=BLUE, after=7): return Kicker(text, color, after=after)
def tracked(c, x, y, text, font="PJS-B", size=7.3, color=BLUE, space=1.15, right=False):
    w = pdfmetrics.stringWidth(text, font, size) + space * (len(text) - 1)
    c.saveState(); t = c.beginText(x - w if right else x, y); t.setFont(font, size); t.setCharSpace(space); t.setFillColor(color); t.textLine(text); c.drawText(t); c.restoreState()

CLEAN = os.path.join(HERE, "charts_clean")
def chart_path(name):
    c = os.path.join(CLEAN, name + ".png")
    return c if os.path.exists(c) else os.path.join(CHD, name + ".png")
def img(path, width):
    from PIL import Image as PI
    w, h = PI.open(path).size; return Image(path, width=width, height=width * h / w)
def G(name, width=CW, max_h=4.9 * inch):
    from PIL import Image as PI
    w, h = PI.open(chart_path(name)).size
    if width * h / w > max_h: width = max_h * w / h
    im = img(chart_path(name), width); im.hAlign = "CENTER"; return im
def card(flows, width=CW, bg=CARD2, pad=12, border=LINE, radius=9):
    t = Table([[flows]], colWidths=[width]); t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("BOX", (0, 0), (-1, -1), 0.6, border), ("LEFTPADDING", (0, 0), (-1, -1), pad),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad), ("TOPPADDING", (0, 0), (-1, -1), pad - 1), ("BOTTOMPADDING", (0, 0), (-1, -1), pad), ("ROUNDEDCORNERS", [radius] * 4)])); return t
def grid(cells, widths):
    t = Table([cells], colWidths=widths); t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0), ("VALIGN", (0, 0), (-1, -1), "TOP")])); return t
def tiles(items, color=GREEN):
    n = len(items); gap = 9; cw = (CW - gap * (n - 1)) / n; cells, widths = [], []
    for i, it in enumerate(items):
        st = ParagraphStyle("n%d" % i, parent=ST["num"], textColor=color)
        cells.append(card([Paragraph(esc(it["value"]), st), Spacer(1, 3), P(esc(it["label"]), "numlab")], width=cw, pad=11)); widths.append(cw)
        if i < n - 1: cells.append(""); widths.append(gap)
    return grid(cells, widths)
def dtable(columns, rows, widths=None, small=False):
    hs, cs, cw_ = ("cellh", "acell" if small else "cell", "acellw" if small else "cellw")
    data = [[P(esc(c).upper(), hs) for c in columns]] + [[P(esc(x, 6.3 if small else 7.0), cw_ if j == 0 else cs) for j, x in enumerate(r)] for r in rows]
    if not widths:
        first = min(1.9 * inch, max(1.1 * inch, CW * 0.26)); widths = [first] + [(CW - first) / (len(columns) - 1)] * (len(columns) - 1)
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, 0), 0.6, LINE2), ("LINEBELOW", (0, 1), (-1, -1), 0.35, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 3.4), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.4)])); return t
def auto_widths(columns, rows, minw=0.86 * inch):
    """Column widths proportional to content length (capped), so short columns stop wasting space."""
    L = [max([len(str(c))] + [min(len(str(r[j])), 60) for r in rows]) for j, c in enumerate(columns)]
    tot = sum(L); w = [max(minw, CW * l / tot) for l in L]; w[0] = max(w[0], 1.05 * inch); k = CW / sum(w); return [x * k for x in w]

class Dot(Flowable):
    def __init__(self, color, w): super().__init__(); self.c = color; self.w = w
    def wrap(self, aw, ah): return (self.w, 9)
    def draw(self):
        c = self.canv; c.setFillColor(CANVAS); c.circle(self.w, 4.2, 5.2, stroke=0, fill=1)
        c.setFillColor(self.c); c.circle(self.w, 4.2, 3.4, stroke=0, fill=1)
def steps_table(steps, color):
    """Vertical timeline: time | rail dot | what happened | first public post."""
    RAIL = 0.20 * inch; TW = 0.92 * inch; SW = 1.42 * inch; BW = CW - TW - RAIL - SW
    rows = []
    for s in steps:
        rows.append([P(esc(s["t"]), "steptime"), Dot(color, RAIL), [P(esc(s["title"]), "steptitle"), P(esc(s["body"], 7.6), "stepbody")],
                     [P("FIRST PUBLIC", "seenlab"), P(esc(s.get("seen", "")), "seen")]])
    t = Table(rows, colWidths=[TW, RAIL, BW, SW])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBEFORE", (2, 0), (2, -1), 1.1, tint(color, 0.55)),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("LEFTPADDING", (2, 0), (2, -1), 16), ("RIGHTPADDING", (2, 0), (2, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 13), ("LINEBELOW", (2, 0), (-1, -2), 0.35, LINE)]))
    return t
def receipts(rs):
    cards = [card([P(f'<font name="Butler" size="15" color="#6EA6F8">“</font> {esc(r.get("quote", ""))}', "quote"), Spacer(1, 6),
                   P(f'{esc(r.get("who", ""))}  ·  {esc(r.get("utc", ""))} UTC  ·  {esc(r.get("interactions", ""))}', "quotem")], width=(CW - 9) / 2, bg=CARD, pad=10) for r in rs[:4]]
    out = []
    for i in range(0, len(cards), 2):
        pair = cards[i:i + 2]; out += [grid([pair[0], "", pair[1] if len(pair) > 1 else ""], [(CW - 9) / 2, 9, (CW - 9) / 2]), Spacer(1, 9)]
    return out
def fmt_int(n):
    n = float(n or 0)
    for d, s in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if n >= d: return (f"{n / d:.1f}" if n / d < 100 else f"{n / d:.0f}") + s
    return f"{n:.0f}"

# ---------------------------------------------------------------- data
P1 = json.load(open(os.path.join(ROOT, "part1.json"))); SYN = json.load(open(os.path.join(ROOT, "synthesis.json"))); A = json.load(open(os.path.join(ROOT, "analysis.json")))
for t in SYN["night"]["tiles"]: t["label"] = t["label"].replace("(4.6 event hours)", "(five hourly buckets)")
SYN["about"]["paras"] = [x.replace("to see attention move before price does", "to measure attention across networks in real time") for x in SYN["about"]["paras"] if "joe@" not in x and "re-pulled" not in x]
def chap(k):
    for d in ("chapters_v2", "chapters"):
        p = os.path.join(ROOT, d, k + ".json")
        if os.path.exists(p): return json.load(open(p))
FLOW = next((json.load(open(q)) for q in (os.path.join(ROOT, "chapters_v2", "flow.json"), os.path.join(ROOT, "chapters", "flow_verified.json")) if os.path.exists(q)), None)
SOCIAL = ["shock", "firsthour", "reach", "official", "narratives", "sentiment", "newcomers", "networks", "stablecoins", "exchanges", "market", "history", "claims", "watch"]
TITLES = {"shock": "The attention shock", "firsthour": "The first hour: who broke it", "reach": "Who carried the reach", "official": "The official response", "narratives": "Narrative forks",
          "sentiment": "The sentiment regime", "newcomers": "The newcomers", "networks": "Where it lived", "stablecoins": "The freeze became the story", "exchanges": "Exchange spillover",
          "market": "Bitcoin, BNB and the tape", "history": "How it compares", "claims": "The claim ledger", "watch": "The unfinished curve", "prevention": "Could it have been stopped?",
          "forensics": "The technical record", "flow": "The money"}
CHARTS = {"shock": ["g_event_multiples", "g_minute_cum"], "firsthour": ["g_breakers"], "reach": ["g_classes"], "official": ["g_official"], "narratives": ["g_themes", "g_themes_hour", "g_keywords"],
          "sentiment": ["g_sent_week", "g_sent_event", "g_sent_network", "g_sent_delta"], "newcomers": ["g_newcomers", "g_spam"], "networks": ["g_network_share", "g_network_timing"],
          "stablecoins": ["g_contagion_lines"], "exchanges": ["g_contagion", "g_exchanges"], "market": ["g_crypto_top"], "history": ["g_bybit_vs", "g_comp_daily", "g_1y"], "claims": ["g_claims"],
          "prevention": ["g_scenarios_none"], "watch": ["g_cum"], "flow": ["g_flow_v2", "g_positions_v2"]}
SMALL = {"g_sent_network", "g_sent_delta", "g_spam", "g_classes", "g_exchanges", "g_crypto_top"}
KICK = {"g_event_multiples": "Event hours vs baseline", "g_minute_cum": "Minute by minute, sampled posts", "g_breakers": "The first two hours", "g_creators": "Top 20 accounts", "g_classes": "Engagement by account class",
        "g_official": "Every official post", "g_themes": "Themes by engagement", "g_themes_hour": "Themes by hour", "g_keywords": "Phrases, 24h vs prior 24h", "g_sent_week": "Sentiment, seven days",
        "g_sent_event": "Sentiment by hour and topic", "g_sent_network": "Sentiment by network", "g_sent_delta": "Sentiment change by topic", "g_newcomers": "First-time posters", "g_spam": "Spam share",
        "g_network_share": "Engagements and posts by network, 24h", "g_network_timing": "When each network arrived", "g_contagion_lines": "Related topics, hour by hour", "g_contagion": "Attention spillover",
        "g_exchanges": "Share of exchange conversation", "g_crypto_top": "Top crypto topics, 24h", "g_bybit_vs": "Hour for hour vs Bybit", "g_comp_daily": "Peak day vs baseline, five events", "g_1y": "Binance, 365 days",
        "g_claims": "The loss figure by minute", "g_cum": "Cumulative engagements", "g_scenarios": "Two historical shapes", "g_operator_v2": "Every operator transaction, Oct 28 to 30", "g_hijack_v2": "What left Binance 14 while it ran the attacker's code",
        "g_flow_v2": "Where the funds went, by chain and status", "g_positions_v2": "Every verified position", "g_master_gantt": "October 28 to 30, all lanes", "g_night_gantt": "20:00 to 01:00 UTC, lane by lane",
        "g_freeze_ladder": "Announced freezes vs Binance's verified total", "g_detect_lag": "From chain to feed"}
CAP = {"g_event_multiples": "Each event hour against the Binance topic's own 7-day hourly mean.", "g_minute_cum": "Cumulative engagement of the 686 sampled posts by posting minute.",
       "g_breakers": "Every sampled post over 100K engagements in the first two hours. Green official, blue aggregators, purple large accounts, amber mid, pink small.", "g_creators": "Sampled posts, 20:24 to 01:00 UTC.",
       "g_classes": "Share of sampled engagement by account class.", "g_official": "Every post by @cz_binance, @binance and @heyibinance, log scale.", "g_themes": "Keyword-matched themes in the sampled posts.",
       "g_themes_hour": "Theme mentions by posting hour.", "g_keywords": "Rolling 24h post counts, last 24h vs prior 24h. Log scale.", "g_sent_week": "Engagement-weighted sentiment per hour, 0 to 100.",
       "g_sent_event": "Sentiment per hour for Binance and related topics; 'pre' is the 7-day mean.", "g_sent_network": "Binance topic, last 24h.", "g_sent_delta": "Event hours vs 7-day mean.",
       "g_newcomers": "Accounts posting on Binance for the first time in LunarCrush's lookback.", "g_spam": "Spam-classified share of active posts.", "g_network_share": "Binance topic, last 24h.",
       "g_network_timing": "Posting time of sampled posts, by network.", "g_contagion_lines": "Hourly engagements as a multiple of each topic's 7-day mean, log scale.",
       "g_contagion": "Peak hourly multiple, 20:00 to 00:00 UTC. Amber: already elevated at 20:00.", "g_exchanges": "Share of the exchange category's engagements, last 24h.", "g_crypto_top": "Cryptocurrencies by 24h engagements, Binance inserted for scale.",
       "g_bybit_vs": "Both events aligned to the first exploit hour, scaled to their own prior-week means.", "g_comp_daily": "Peak day as a multiple of the prior 14 days (Binance: 1-year median day).", "g_1y": "Engagements per UTC day.",
       "g_claims": "Loss figures as posted, by minute; dot size is engagement. Green: net of freezes.", "g_cum": "Cumulative engagements since 20:00 UTC (bars), active creators per hour (line).", "g_scenarios": "Daily engagements as a share of each event's peak day.",
       "g_operator_v2": "The operator 0x7C86 and the wallets that funded it. Dashed line: the sweep, 20:24:23 Oct 29.", "g_hijack_v2": "Value leaving Binance 14 and Hot Wallet 34, log scale. The sweep bar counts the USDT and ETH lines only; 62 smaller tokens moved with them.",
       "g_flow_v2": "US dollars. Balances read live 03:20 to 03:27 UTC Oct 30; prices CoinGecko 03:22 UTC; stablecoins at face. Freeze status read from each token contract. The BTC, Tron, XRP and SOL legs are attributed to Binance by Whale Alert labels and timing.", "g_positions_v2": "Same read. Red: unfrozen. Green: frozen, recovered or immobilised.",
       "g_master_gantt": "Left: the setup, Oct 28 06:00 to Oct 29 20:00. Right: the attack night at 7.6 times the scale. Every mark is a verified transaction or a timestamped public statement.",
       "g_night_gantt": "Shaded: the 3 hours 49 minutes Binance 14 ran the attacker's code. *XRP and SOL senders are Binance by Whale Alert's label; Binance has not said whether these were its own transfers. Bottom: hourly engagements on the Binance topic.",
       "g_freeze_ladder": "Green: running sum of issuer announcements (Ripple's ~200M excluded). Amber: totals Binance verified.",
       "g_detect_lag": "Minutes from each on-chain event to the first public post that described it. Blue: setup. Red: the attack."}
TALLOK = {"g_night_gantt": 7.6 * inch, "g_positions_v2": 6.0 * inch, "g_week_hourly": 2.5 * inch}
def GK(name, width=CW):
    if not os.path.exists(chart_path(name)): return Spacer(1, 0)
    return KeepTogether([K(KICK.get(name, "")), G(name, width, TALLOK.get(name, 4.9 * inch)), P(esc(CAP.get(name, ""), 7.0), "caption")])

# ---------------------------------------------------------------- page chrome
LOGO = os.path.join(HERE, "lc-logo-horizontal-white.png"); BG = chart_path("cover_bg")
class Doc(BaseDocTemplate):
    def __init__(self, fn):
        super().__init__(fn, pagesize=letter, leftMargin=M, rightMargin=M, topMargin=M + 0.3 * inch, bottomMargin=M, title="The Binance Hack, Reconstructed", author="LunarCrush",
                         subject="A step-by-step reconstruction of the Oct 29, 2026 Binance hot-wallet hack from the chain and from social data", creator="LunarCrush")
        fr = Frame(M, M, CW, H - 2 * M - 0.3 * inch, id="f", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0); full = Frame(0, 0, W, H, id="c", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate("cover", [full], onPage=cover_page), PageTemplate("body", [fr], onPage=body_page), PageTemplate("opener", [fr], onPage=opener_page),
                               PageTemplate("part", [full], onPage=part_page)])
def bg(c): c.setFillColor(CANVAS); c.rect(0, 0, W, H, stroke=0, fill=1)
def chrome(c, doc):
    c.drawImage(LOGO, M, H - M + 0.04 * inch, width=1.0 * inch, height=1.0 * inch * 263 / 1000, mask="auto")
    tracked(c, W - M, H - M + 0.09 * inch, "THE BINANCE HACK  ·  RECONSTRUCTED", "PJS-SB", 6.6, MUTED, 1.0, right=True)
    c.setStrokeColor(LINE); c.setLineWidth(0.6); c.line(M, H - M - 0.1 * inch, W - M, H - M - 0.1 * inch)
    tracked(c, M, M - 0.42 * inch, "LUNARCRUSH  ·  OCTOBER 2026", "PJS-SB", 6.4, MUTED, 1.0)
    c.setFont("PJS-B", 7.4); c.setFillColor(WHITE); c.drawRightString(W - M, M - 0.42 * inch, f"{doc.page:02d}")
def body_page(c, doc): bg(c); chrome(c, doc)
def opener_page(c, doc):
    bg(c); num = getattr(doc, "_num", "")
    c.saveState(); c.setFont("Butler", 230); c.setFillColor(Color(1, 1, 1, 0.03)); c.drawRightString(W - M + 8, H - 3.3 * inch, num); c.restoreState(); chrome(c, doc)
def part_page(c, doc):
    c.drawImage(BG, 0, 0, width=W, height=H); info = getattr(doc, "_part", ("", "", ""))
    c.saveState(); c.setFont("Butler", 420); c.setFillColor(Color(1, 1, 1, 0.035)); c.drawRightString(W - 0.4 * inch, 1.2 * inch, info[0]); c.restoreState()
    c.drawImage(LOGO, M, H - M - 0.1 * inch, width=1.25 * inch, height=1.25 * inch * 263 / 1000, mask="auto")
    tracked(c, M, H * 0.52, f"PART {info[0]}", "PJS-B", 8.4, GREEN, 1.6)
    c.setFont("Butler", 50); c.setFillColor(WHITE); c.drawString(M - 2, H * 0.52 - 0.8 * inch, info[1])
    p = Paragraph(esc(info[2]), ST["coversub"]); w, h = p.wrap(4.9 * inch, 3 * inch); p.drawOn(c, M, H * 0.52 - 1.15 * inch - h)
def cover_page(c, doc):
    C = P1["cover"]; c.drawImage(BG, 0, 0, width=W, height=H)
    c.drawImage(LOGO, M, H - M - 0.12 * inch, width=1.5 * inch, height=1.5 * inch * 263 / 1000, mask="auto")
    tracked(c, W - M, H - M - 0.04 * inch, "LUNARCRUSH RESEARCH", "PJS-B", 7.2, MUTED, 1.4, right=True)
    tracked(c, M, H - 2.05 * inch, C["kicker"], "PJS-B", 7.8, GREEN, 1.5)
    c.setFont("Butler", 58); c.setFillColor(WHITE); c.drawString(M - 3, H - 2.95 * inch, C["title"])
    c.setFont("Butler", 28); c.setFillColor(HexColor("#D9DDE7")); c.drawString(M - 1, H - 3.55 * inch, C["subtitle"])
    p = Paragraph(esc(C["sub"]), ST["coversub"]); w, h = p.wrap(5.3 * inch, 2 * inch); p.drawOn(c, M, H - 3.95 * inch - h)
    art = chart_path("g_cover_art")
    from PIL import Image as PI
    aw, ah = PI.open(art).size; dw = CW + 0.1 * inch; c.drawImage(art, M - 0.05 * inch, 2.05 * inch, width=dw, height=dw * ah / aw, mask="auto")
    c.setStrokeColor(LINE2); c.setLineWidth(0.6); c.line(M, 1.62 * inch, W - M, 1.62 * inch)
    stats = C["stats"]; gap = 0.18 * inch; cw = (CW - gap * (len(stats) - 1)) / len(stats)
    for i, (v, l) in enumerate(stats):
        x = M + i * (cw + gap); c.setFont("PJS-XB", 20); c.setFillColor(WHITE); c.drawString(x, 1.22 * inch, v)
        q = Paragraph(esc(l), ST["coverlab"]); qw, qh = q.wrap(cw, 0.6 * inch); q.drawOn(c, x, 1.12 * inch - qh)
    tracked(c, M, 0.55 * inch, "SOURCES: ETHEREUM MAINNET, LUNARCRUSH (X, TIKTOK, YOUTUBE, INSTAGRAM, REDDIT, NEWS)", "PJS-SB", 6.0, MUTED, 0.9)
    tracked(c, W - M, 0.55 * inch, "LUNARCRUSH.COM", "PJS-B", 6.4, WHITE, 1.2, right=True)
class SetAttr(Flowable):
    def __init__(self, **kw): super().__init__(); self.kw = kw; self.width = self.height = 0
    def draw(self):
        for k, v in self.kw.items(): setattr(self.canv._doctemplate, k, v)
    def wrap(self, *a): return (0, 0)

# ---------------------------------------------------------------- story
story = [NextPageTemplate("body"), PageBreak()]
n = 0
def num():
    global n; n += 1; return f"{n:02d}"
def opener(kicker, title, headline=None, dek=None, nums=None, color=GREEN, numstr="", h1="h1", lead="lead"):
    out = [NextPageTemplate("opener"), SetAttr(_num=numstr), PageBreak(), K(kicker), P(esc(title), h1)]
    out += [NextPageTemplate("body")]
    if headline: out.append(P(esc(headline), "headline"))
    if dek: out.append(P(esc(dek), lead))
    if nums: out += [tiles(nums, color), Spacer(1, 12 if lead == "leads" else 16)]
    return out
def part(roman, title, line):
    return [NextPageTemplate("part"), SetAttr(_part=(roman, title, line)), PageBreak(), Spacer(1, 1), NextPageTemplate("body")]

# contents (filled after numbering is known)
toc_rows = []; story_body = []
def T(numstr, title, desc, part_label=None):
    if part_label: toc_rows.append(("", part_label, ""))
    toc_rows.append((numstr, title, desc))

# 01 summary
E = P1["exec"]; s = num(); T(s, "Summary", E["title"])
story_body += opener(f"{s}  ·  Summary", E["title"], None, E["lead"], E["numbers"], numstr=s, h1="h1s", lead="leads")
for i, f in enumerate(E["findings"], 1):
    story_body.append(KeepTogether([P(f'<font color="#14B881" name="PJS-XB">{i:02d}</font>&nbsp;&nbsp;&nbsp;{esc(f["title"])}', "h3"), P(esc(f["body"]), "fbody")]))
# 02 overview
O = P1["overview"]; s = num(); T(s, O["title"], "The setup, the attack and the response on one clock")
story_body += opener(f"{s}  ·  Overview", O["title"], None, O["lead"], numstr=s) + [GK("g_master_gantt"), Spacer(1, 6)]
acts = O["acts"]; cw3 = (CW - 18) / 3
def actcard(a):
    return card([Paragraph(f'<font name="Butler" size="20" color="#14B881">{a["n"]}</font>', ST["body"]), P(esc(a["title"]), "cardt"), P(esc(a["when"]), "seenlab"), Spacer(1, 3), P(esc(a["line"]), "cardb")], width=cw3, pad=10)
story_body += [grid([actcard(acts[0]), "", actcard(acts[1]), "", actcard(acts[2])], [cw3, 9, cw3, 9, cw3]), Spacer(1, 9),
               grid([actcard(acts[3]), "", actcard(acts[4]), "", actcard(acts[5])], [cw3, 9, cw3, 9, cw3])]

# PART I: the hack
story_body += part("I", "The hack", "Six acts, from the first mixer withdrawal to the revocation, each step verified on-chain and matched to the first public post that described it.")
toc_rows.append(("", "PART I  ·  THE HACK", ""))
for act in P1["acts"]:
    if act["key"] == "act6": continue
    s = num(); col = ACT[act["color"]]; T(s, f'Act {act["n"]}: {act["title"]}', act["headline"])
    story_body += opener(f'{s}  ·  Act {act["n"]}', act["title"], act["headline"], act["dek"], color=col, numstr=s)
    if act["key"] == "act2": story_body += [steps_table(act["steps"], col), PageBreak(), GK(act["chart"])]
    else: story_body += [GK(act["chart"]), Spacer(1, 4), steps_table(act["steps"], col)]
# Act V: the money (only from re-verified balances)
if FLOW:
    s = num(); T(s, "Act V: The money", FLOW["headline"])
    story_body += opener(f"{s}  ·  Act V", "The money", FLOW["headline"], FLOW["dek"], color=GREEN, numstr=s)
    story_body += [GK("g_flow_v2"), tiles(FLOW["key_numbers"]), Spacer(1, 16)] + [P(esc(p)) for p in FLOW["narrative"] if p.strip()] + [GK("g_positions_v2")]
    tb = FLOW.get("table")
    if tb and tb.get("rows"): story_body += [CondPageBreak(2.2 * inch), K(tb["title"]), dtable(tb["columns"], tb["rows"], auto_widths(tb["columns"], tb["rows"]), small=True), Spacer(1, 10)]
# Act VI
a6 = [a for a in P1["acts"] if a["key"] == "act6"][0]; s = num(); T(s, "Act VI: The public record", a6["headline"])
story_body += opener(f"{s}  ·  Act VI", a6["title"], a6["headline"], a6["dek"], color=VIOLET, numstr=s) + [GK(a6["chart"])] + [P(esc(p)) for p in a6["body"]]

def chapter(k, s):
    ch = chap(k); out = opener(f"{s}  ·  Chapter", TITLES[k], ch["headline"], ch["dek"], ch.get("key_numbers"), numstr=s)
    out += [P(esc(p)) for p in ch["narrative"] if p.strip()]
    charts = [c for c in CHARTS.get(k, []) if os.path.exists(chart_path(c))]
    small = [c for c in charts if c in SMALL]; big = [c for c in charts if c not in SMALL]
    out += [GK(c) for c in big]
    hw = (CW - 14) / 2
    while small:
        a = small.pop(0); b = small.pop(0) if small else None
        left = [K(KICK.get(a, "")), G(a, hw)]; right = [K(KICK.get(b, "")), G(b, hw)] if b else [Spacer(1, 1)]
        out.append(KeepTogether([grid([left, "", right], [hw, 14, hw]), P(esc(CAP.get(a, "") + ("  Right: " + CAP.get(b, "") if b else "")), "caption")]))
    tb = ch.get("table")
    if tb and tb.get("rows"):
        rows = [r for r in tb["rows"] if not any("(partial" in str(c) for c in r)][:14]; out += [CondPageBreak(2.2 * inch), K(tb["title"]), dtable(tb["columns"], rows, auto_widths(tb["columns"], rows), small=True), Spacer(1, 12)]
    if ch.get("receipts"): out += [CondPageBreak(1.9 * inch), K("What the posts said")] + receipts(ch["receipts"])
    cos = [c for c in ch.get("callouts", []) if c.get("title")][:2]
    if cos:
        hw2 = (CW - 9) / 2; cards = [card([P(esc(x["title"]), "cardt"), P(esc(x["body"]), "cardb")], width=hw2, bg=tint(GREEN, 0.09), border=tint(GREEN, 0.28), pad=11) for x in cos]
        out += [CondPageBreak(1.3 * inch), K("Takeaways", GREEN), grid([cards[0], "", cards[1] if len(cards) > 1 else ""], [hw2, 9, hw2]), Spacer(1, 12)]
    w = [x for x in ch.get("watch", []) if x][:3]
    if w: out += [CondPageBreak(1.0 * inch), card([K("Next 24 to 72 hours", AMBER)] + [P(f'<font color="#F2A93B" name="PJS-B">{j}</font>&nbsp;&nbsp;{esc(x)}', "smallw") for j, x in enumerate(w, 1)], pad=11)]
    return out

# Could it have been stopped (closes Part I)
s = num(); T(s, TITLES["prevention"], chap("prevention")["headline"]); story_body += chapter("prevention", s)

# PART II: how the world found out
story_body += part("II", "How the world found out", "95 million engagements in the first five hours: who broke the story, how it was framed, where it travelled and what it did to the rest of the market.")
toc_rows.append(("", "PART II  ·  HOW THE WORLD FOUND OUT", ""))
N = SYN["night"]; s = num(); T(s, "The night in numbers", "Nine counts and the hourly ledger")
story_body += opener(f"{s}  ·  Part II", "The night in numbers", N["title"], None, numstr=s) + [tiles(N["tiles"][:3]), Spacer(1, 9), tiles(N["tiles"][3:6]), Spacer(1, 9), tiles(N["tiles"][6:9]), Spacer(1, 16)]
hb = A["binance_hourly"]; base = hb["baseline"]
hrows = [["7-day mean hour", fmt_int(base["interactions"]), "1.0x", f'{base["posts_created"]:.0f}', "1.0x", f'{base["contributors_created"]:.0f}', f'{base["contributors_active"]:,.0f}', f'{base["sentiment"]:.0f}']]
for h in hb["post"]:
    if h["partial"]: continue
    hrows.append([h["utc"], fmt_int(h["interactions"]), f'{h["x_base"]:.1f}x', f'{h["posts_created"]:,}', f'{h["x_posts"]:.1f}x', f'{h["contributors_created"]:,}', f'{h["contributors_active"]:,}', f'{h["sentiment"]}'])
story_body += [GK("g_week_hourly"), KeepTogether([K("The hourly ledger, Binance topic (UTC)"), dtable(["Hour", "Eng.", "x mean", "New posts", "x mean", "First-time", "Active", "Sentiment"], hrows, [1.25 * inch] + [(CW - 1.25 * inch) / 7] * 7)])]
TL = SYN["timeline"]; s = num(); T(s, "Minute by minute", "Chain, social, Binance and issuers on one clock")
story_body += opener(f"{s}  ·  Part II", "Minute by minute", "Chain, social, Binance and issuers on one clock", None, numstr=s)
trows = [[r["utc"], r["lane"], r["what"].replace(" (unit not stated in the post)", ""), r["eng"]] for r in TL["rows"] if r["lane"] != "Data"]
story_body += [dtable(["UTC", "Lane", "What happened", "Engagements"], trows, [0.55 * inch, 0.75 * inch, CW - 2.15 * inch, 0.85 * inch], small=True)]
for k in SOCIAL:
    s = num(); T(s, TITLES[k], chap(k)["headline"]); story_body += chapter(k, s)

# Appendix
toc_rows.append(("", "APPENDIX", ""))
s = num(); T(s, TITLES["forensics"], "The full on-chain account, with addresses and transactions"); story_body += chapter("forensics", s)
s = num(); T(s, "Sources and definitions", "Data, baselines and terms")
METH = [("Sources", "Social data: LunarCrush (X, TikTok, YouTube, Instagram, Reddit and about 10,000 news sites), pulled 01:00 to 01:30 UTC Oct 30. On-chain: Ethereum via public JSON-RPC and the Blockscout API; Act V balances and transfers read live on Ethereum, Bitcoin, Tron, XRP Ledger, Solana and Arbitrum, 03:20 to 03:27 UTC Oct 30. Attribution of the Bitcoin, Tron, XRP and Solana senders to Binance: Whale Alert labels. Prices: CoinGecko."),
        ("Engagements", "Likes, reposts, replies, comments and views-weighted interactions, summed across networks."),
        ("Baseline", "The Binance topic's mean hour over the 162 full hours from 02:00 UTC Oct 23 to 19:00 UTC Oct 29: 1.0M engagements, 418 new posts, 293 first-time posters, sentiment 80. 'x mean' divides an event hour by it."),
        ("First-time posters", "Accounts posting on the topic for the first time in LunarCrush's lookback."),
        ("Sentiment", "Of engagement on posts scored positive or negative, the share that was positive, 0 to 100."),
        ("Sampled posts", "686 top posts published between 20:14 UTC Oct 29 and 01:00 UTC Oct 30 that mention the event. Used for who-said-what, themes, account classes and timing."),
        ("Comparables", "Bybit (Feb 21, 2025) hour for hour; FTX (Nov 2022) and the CZ plea (Nov 21, 2023) as daily series.")]
story_body += opener(f"{s}  ·  Appendix", "Sources and definitions", numstr=s)
story_body += [grid([P(esc(a), "h3"), "", P(esc(b), "smallw")], [1.5 * inch, 12, CW - 1.5 * inch - 12]) for a, b in METH]
story_body += [Spacer(1, 6)]
s = num(); T(s, "Tables", "Spillover, keywords, top 40 posts")
story_body += opener(f"{s}  ·  Appendix", "Tables", numstr=s)
rows = [[c["display"], fmt_int(c["base_int_h"]), fmt_int(c["peak_int_h"]), f'{c["peak_x"]:.1f}x', c["peak_utc"], f'{c["x_posts_5h"]:.1f}x', f'{c["x_newcreators_5h"]:.1f}x', f'{c["sent_pre"]:.0f}', f'{c["sent_post"]:.0f}'] for c in A["contagion"] if c["topic"] not in ("coin", "tornado")]
story_body += [K("A1  ·  Attention spillover, 20:00 to 00:00 UTC"), dtable(["Topic", "Mean/h", "Peak/h", "Peak x", "Peak hour", "Posts x", "New x", "Sent. mean", "Sent. event"], rows, [1.45 * inch] + [(CW - 1.45 * inch) / 8] * 8, small=True), Spacer(1, 14)]
kw = A["keywords"]; rows = [[v["display"], f'{v["posts_prev"] or 0:,}', f'{v["posts_24h"] or 0:,}', f'{v["creators_prev"] or 0:,}', f'{v["creators_24h"] or 0:,}'] for k_, v in kw.items() if v.get("posts_24h") and v["display"].lower() not in ("lazarus", "north korea")]
story_body += [CondPageBreak(2.5 * inch), K("A2  ·  Keywords, rolling 24h vs prior 24h"), dtable(["Phrase", "Posts, prior 24h", "Posts, last 24h", "Creators, prior", "Creators, last 24h"], rows, small=True), Spacer(1, 14)]
def trunc(t, n=118):
    t = " ".join(clean(t).split())
    return t if len(t) <= n else t[:t.rfind(" ", 0, n)].rstrip(",;:") + "…"
rows = [[f'@{p["creator"]}', p["utc"][-5:], p["type"].replace("-video", "").replace("-post", ""), fmt_int(p["followers"]), fmt_int(p["interactions"]), trunc(p["text"])] for p in [q for q in A["top_posts"] if q["creator"] != "LizardX"][:40]]
story_body += [CondPageBreak(3 * inch), K("A3  ·  Top 40 sampled posts by engagement"), dtable(["Account", "UTC", "Net", "Followers", "Eng.", "Text, as posted"], rows, [1.12 * inch, 0.5 * inch, 0.48 * inch, 0.78 * inch, 0.5 * inch, CW - 3.38 * inch], small=True), Spacer(1, 14)]
story_body += [CondPageBreak(2.6 * inch), Spacer(1, 16), K("About LunarCrush"), P(esc(SYN["about"]["title"]), "h2")] + [P(esc(p)) for p in SYN["about"]["paras"]]

# contents page
story += [K("Contents"), P("Inside this report", "h2"), Spacer(1, 2)]
rows = []
for nn, t, d in toc_rows:
    if not nn: rows.append([Kicker(t, GREEN, size=6.8, after=2), "", ""])
    else: rows.append([P(f'<font color="#6EA6F8" name="Mono-M">{nn}</font>', "toc"), P(f'<font color="#FFFFFF">{esc(t)}</font>', "toc"), P(esc(d), "tocd")])
tt = Table(rows, colWidths=[0.42 * inch, 2.2 * inch, CW - 2.62 * inch])
sty = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 1.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6)]
for i, (nn, t, d) in enumerate(toc_rows):
    if nn: sty.append(("LINEBELOW", (0, i), (-1, i), 0.35, LINE))
    else: sty += [("SPAN", (0, i), (-1, i)), ("TOPPADDING", (0, i), (-1, i), 9)]
tt.setStyle(TableStyle(sty)); story += [tt] + story_body

out = os.path.join(ROOT, "LunarCrush-Binance-Hack-Reconstructed-2026-10-29.pdf")
Doc(out).build(story); print("wrote", out)
