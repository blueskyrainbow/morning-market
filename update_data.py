"""매일 시세를 받아 data.json 을 만드는 스크립트 (GitHub Actions에서 자동 실행)"""
import json, datetime
import yfinance as yf

def last2(sym):
    c = yf.Ticker(sym).history(period="10d")["Close"].dropna()
    return float(c.iloc[-1]), (float(c.iloc[-1]) / float(c.iloc[-2]) - 1) * 100, c.index[-1].strftime("%m/%d")

def row(name, sym, fmt=None):
    v, p, d = last2(sym)
    return [name, fmt(v) if fmt else round(v, 2), round(p, 2)], d

def word(p):
    return "상승" if p > 0.1 else "하락" if p < -0.1 else "보합"

us, us_d = zip(*[row(n, s) for n, s in [("다우존스", "^DJI"), ("S&P500", "^GSPC"), ("나스닥", "^IXIC")]])
kr, kr_d = zip(*[row(n, s) for n, s in [("코스피", "^KS11"), ("코스닥", "^KQ11")]])
comma = lambda v: f"{v:,.2f}"
macro = [row(n, s, comma)[0] for n, s in [("원/달러 환율", "KRW=X"), ("미 국채 10년물(%)", "^TNX"),
         ("WTI 유가($)", "CL=F"), ("금($/oz)", "GC=F"), ("VIX", "^VIX")]]

us_avg = sum(r[2] for r in us) / len(us)
line = lambda rows: ", ".join(f"{r[0]} {r[2]:+.2f}%" for r in rows)
try:
    manual = json.load(open("manual.json", encoding="utf-8"))
except Exception:
    manual = {}

data = {
    "headline": f"미국 증시 {word(us_avg)}, 코스피 {word(kr[0][2])} 마감",
    "lead": "전일 지수 등락률을 자동 집계한 요약입니다.",
    "us": {"when": f"{us_d[0]} 마감 기준", "idx": list(us), "text": [line(us)]},
    "kr": {"when": f"{kr_d[0]} 마감 기준", "idx": list(kr), "text": [line(kr)]},
    "macro": macro,
    "check": manual.get("check", []),
    "comment": manual.get("comment", ""),
    "updated": datetime.datetime.utcnow().isoformat() + "Z",
}
json.dump(data, open("data.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
