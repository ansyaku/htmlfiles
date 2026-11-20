#!/usr/bin/env python3
"""Ambil harga, valuasi, dan data fundamental harian untuk semua saham di data/universe.json -> data/quotes.json.
Sumber: Yahoo Finance via yfinance (tidak resmi, bisa berubah/rate-limit). Nilai yang gagal diambil
dipertahankan dari data sebelumnya agar halaman tidak kosong."""
import json, time, datetime as dt, pathlib, sys, math
import pandas as pd
import yfinance as yf

ROOT = pathlib.Path(__file__).resolve().parent.parent
UNI = json.loads((ROOT / "data/universe.json").read_text())
OUT = ROOT / "data/quotes.json"
prev = json.loads(OUT.read_text()) if OUT.exists() else {"quotes": {}}
quotes = prev.get("quotes", {})
KEYS = ("p", "d1", "ytd", "y1", "cap", "pe", "dy",
        "npm", "roe", "der", "cr", "nde", "ic", "fcf", "fcfni", "revUp", "revN", "epsUp", "epsN", "revCg", "epsCg")

def ysym(t): return t.replace(".", "-")          # BRK.B -> BRK-B
syms = {u["t"]: ysym(u["t"]) for u in UNI}
fin_set = {u["t"] for u in UNI if u["s"] == "Financials"}   # CR/DER/IC/FCF tidak bermakna untuk bank & asuransi

def ok(x): return x is not None and not (isinstance(x, float) and math.isnan(x))
def r(x, n=2): return round(float(x), n) if ok(x) else None
def pct(a, b): return round((a / b - 1) * 100, 2) if ok(a) and ok(b) and b else None

def row(df, *labels):
    """Ambil baris laporan sebagai Series (lama -> baru), tanpa NaN."""
    if df is None or df.empty: return pd.Series(dtype=float)
    for l in labels:
        if l in df.index:
            return df.loc[l].dropna().sort_index()
    return pd.Series(dtype=float)

def trend(s):
    """(jumlah kenaikan YoY, jumlah periode YoY, CAGR%) dari maksimal 4 titik tahunan terakhir."""
    s = s.tail(4)
    if len(s) < 2: return None, None, None
    up = int(sum(1 for i in range(1, len(s)) if s.iloc[i] > s.iloc[i - 1]))
    cg = None
    if s.iloc[0] > 0 and s.iloc[-1] > 0:
        cg = round(((s.iloc[-1] / s.iloc[0]) ** (1 / (len(s) - 1)) - 1) * 100, 1)
    return up, len(s) - 1, cg

def fundamentals(t, tk):
    info = tk.info
    f = {}
    mc, pe, dr = info.get("marketCap"), info.get("trailingPE"), info.get("dividendRate")
    f["cap"] = round(mc / 1e9, 1) if mc else None
    f["pe"] = round(pe, 1) if ok(pe) and pe > 0 else None
    f["_dr"] = dr
    f["npm"] = r(info["profitMargins"] * 100, 1) if ok(info.get("profitMargins")) else None
    inc = tk.financials
    rev, eps = row(inc, "Total Revenue", "Operating Revenue"), row(inc, "Diluted EPS", "Basic EPS")
    f["revUp"], f["revN"], f["revCg"] = trend(rev)
    f["epsUp"], f["epsN"], f["epsCg"] = trend(eps)
    bs = tk.balance_sheet
    eq = row(bs, "Stockholders Equity", "Common Stock Equity")
    eq = float(eq.iloc[-1]) if len(eq) else None
    roe = info.get("returnOnEquity")
    f["roe"] = r(roe * 100, 1) if ok(roe) and ok(eq) and eq > 0 else None    # ekuitas negatif -> ROE tidak bermakna
    if t in fin_set:
        return f
    debt = row(bs, "Total Debt"); cash = row(bs, "Cash Cash Equivalents And Short Term Investments", "Cash And Cash Equivalents")
    ca, cl = row(bs, "Current Assets"), row(bs, "Current Liabilities")
    cr = info.get("currentRatio")
    if not ok(cr) and len(ca) and len(cl) and cl.iloc[-1]: cr = ca.iloc[-1] / cl.iloc[-1]
    f["cr"] = r(cr)
    f["der"] = r(float(debt.iloc[-1]) / eq) if len(debt) and ok(eq) and eq > 0 else None
    ebitda, ebit, intr = row(inc, "EBITDA", "Normalized EBITDA"), row(inc, "EBIT", "Operating Income"), row(inc, "Interest Expense")
    if len(debt) and len(ebitda) and ebitda.iloc[-1] > 0:
        f["nde"] = r((float(debt.iloc[-1]) - (float(cash.iloc[-1]) if len(cash) else 0)) / float(ebitda.iloc[-1]))
    if len(ebit) and len(intr):
        i = abs(float(intr.iloc[-1])); f["ic"] = r(float(ebit.iloc[-1]) / i, 1) if i > 0 else 99.0
    cf = row(tk.cashflow, "Free Cash Flow"); ni = row(inc, "Net Income")
    if len(cf):
        f["fcf"] = r(float(cf.iloc[-1]) / 1e9, 2)
        if len(ni) and ni.iloc[-1] > 0: f["fcfni"] = r(float(cf.iloc[-1]) / float(ni.iloc[-1]))
    return f

hist = yf.download(list(syms.values()), period="14mo", interval="1d", auto_adjust=True,
                   group_by="ticker", progress=False, threads=True)

last_bar = None
for t, s in syms.items():
    new = {}
    try:
        c = hist[s]["Close"].dropna()
        if len(c) > 2:
            last = float(c.iloc[-1]); last_bar = max(last_bar, c.index[-1]) if last_bar is not None else c.index[-1]
            yr_end = c[c.index < pd.Timestamp(c.index[-1].year, 1, 1)]
            ago = c[c.index <= c.index[-1] - pd.DateOffset(years=1)]
            new.update(p=round(last, 2), d1=pct(last, float(c.iloc[-2])),
                       ytd=pct(last, float(yr_end.iloc[-1])) if len(yr_end) else None,
                       y1=pct(last, float(ago.iloc[-1])) if len(ago) else None)
    except Exception as e:
        print("hist gagal", t, e, file=sys.stderr)
    got_fund = False
    for attempt in range(2):
        try:
            f = fundamentals(t, yf.Ticker(s))
            dr = f.pop("_dr", None)
            new.update(f)
            new["dy"] = round(dr / new["p"] * 100, 2) if ok(dr) and new.get("p") else None
            got_fund = True
            break
        except Exception as e:
            print("fundamental gagal", t, attempt, e, file=sys.stderr); time.sleep(3)
    time.sleep(0.3)
    old = quotes.get(t, {})
    q = {k: (new[k] if new.get(k) is not None else old.get(k)) for k in KEYS}
    if got_fund and "dy" in new and new["dy"] is None: q["dy"] = None     # saham tanpa dividen
    quotes[t] = q

got = sum(1 for q in quotes.values() if q.get("p"))
if got < len(UNI) * 0.5:
    sys.exit(f"Data terlalu sedikit ({got}/{len(UNI)}), tidak menimpa file.")
OUT.write_text(json.dumps({
    "asof": (last_bar.date().isoformat() if last_bar is not None else prev.get("asof")),
    "updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "source": "Yahoo Finance via yfinance",
    "quotes": quotes}, separators=(",", ":")))
print(f"OK {got}/{len(UNI)} saham")
