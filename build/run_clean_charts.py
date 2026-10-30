#!/usr/bin/env python3
"""Re-render the v1 charts WITHOUT their baked-in titles (the v2 PDF labels every chart itself) into build/charts_clean/.
Additive: v1 charts, build_charts.py and charts_index.json are left as they were."""
import os, sys, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import matplotlib; matplotlib.use("Agg")
import matplotlib.axes, matplotlib.figure
matplotlib.axes.Axes.set_title = lambda self, *a, **k: None
matplotlib.figure.Figure.suptitle = lambda self, *a, **k: None
import json as _json
_orig_load = _json.load
def _load(fp, *a, **k):
    d = _orig_load(fp, *a, **k)
    if isinstance(d, dict) and "contagion" in d:   # "tornado" topic is polluted by weather posts: drop it everywhere
        d["contagion"] = [c for c in d["contagion"] if c.get("topic") != "tornado"]
    return d
_json.load = _load
import charts as C

import matplotlib.text as _mtext
_text_init = _mtext.Text.__init__
def _text_init_nocalt(self, *a, **k):  # Plus Jakarta's contextual alternates turn "0x" into "0×"; keep it literal
    _text_init(self, *a, **k); self.set_fontfeatures(["-calt"])
_mtext.Text.__init__ = _text_init_nocalt
C.OUT = os.path.join(HERE, "charts_clean"); os.makedirs(C.OUT, exist_ok=True)
idx = os.path.join(HERE, "charts_index.json"); shutil.copy(idx, idx + ".bak")
try:
    src = os.path.join(HERE, "build_charts.py")
    exec(compile(open(src).read(), src, "exec"), {"__name__": "__main__", "__file__": src})
finally:
    shutil.move(idx + ".bak", idx)
