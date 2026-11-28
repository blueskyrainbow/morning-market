"""Cboe 공식 일별 종가 파일에서 VIX·VIX3M을 받아 vix.json으로 저장(VIX/VIX3M 기간구조 비율)."""
import csv, io, json, sys, urllib.request
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
BASE = "https://cdn.cboe.com/api/global/us_indices/daily_prices/%s_History.csv"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}


def closes(sym):
    req = urllib.request.Request(BASE % sym, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:  # cdn-api.cboe.com 으로 리다이렉트됨
        text = r.read().decode("utf-8", "replace")
    out = {}
    for row in csv.reader(io.StringIO(text)):
        if len(row) < 5 or not row[0][:1].isdigit():
            continue
        m, d, y = row[0].split("/")
        out["%s-%s-%s" % (y, m, d)] = float(row[4])
    return out


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "vix.json"
    v, v3 = closes("VIX"), closes("VIX3M")
    days = sorted(set(v) & set(v3))[-15:]
    hist = [{"date": d, "vix": round(v[d], 2), "vix3m": round(v3[d], 2), "ratio": round(v[d] / v3[d], 4)} for d in days]
    last = hist[-1]
    streak = 0
    for h in reversed(hist):
        if (h["ratio"] >= 1) == (last["ratio"] >= 1):
            streak += 1
        else:
            break
    data = {
        "source": "Cboe daily prices (VIX_History.csv, VIX3M_History.csv)",
        "date": last["date"], "label": last["date"][5:].replace("-", "/"),
        "vix": last["vix"], "vix3m": last["vix3m"], "ratio": last["ratio"],
        "state": "백워데이션" if last["ratio"] >= 1 else "콘탱고", "streak_days": streak,
        "recent": hist,
        "fetched": datetime.now(KST).strftime("%Y-%m-%dT%H:%M+09:00"),
    }
    try:
        old = json.load(open(path, encoding="utf-8"))
        if old.get("recent") == hist:
            print("변화 없음", last); return
    except Exception:
        pass
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("저장:", last, data["state"], streak)


if __name__ == "__main__":
    main()
