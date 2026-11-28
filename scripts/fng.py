"""CNN 공포·탐욕 지수(https://edition.cnn.com/markets/fear-and-greed 원본 데이터)를 fng.json으로 저장.
GitHub Actions에서 실행. 표준 라이브러리만 사용."""
import json, sys, urllib.request
from datetime import datetime, timezone, timedelta

URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
KST = timezone(timedelta(hours=9))
HDR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://edition.cnn.com/",
    "Origin": "https://edition.cnn.com",
}
KO = {"extreme fear": "극단적 공포", "fear": "공포", "neutral": "중립", "greed": "탐욕", "extreme greed": "극단적 탐욕"}
PARTS = [("market_momentum_sp500", "시장 모멘텀"), ("stock_price_strength", "주가 강도"), ("stock_price_breadth", "주가 폭"),
         ("put_call_options", "풋/콜 옵션"), ("market_volatility_vix", "시장 변동성(VIX)"), ("junk_bond_demand", "정크본드 수요"),
         ("safe_haven_demand", "안전자산 수요")]


def kst(ts):
    if isinstance(ts, (int, float)):
        d = datetime.fromtimestamp(ts / 1000, timezone.utc)
    else:
        d = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    return d.astimezone(KST)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "fng.json"
    req = urllib.request.Request(URL, headers=HDR)
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = json.loads(r.read().decode("utf-8"))
    f = raw["fear_and_greed"]
    t = kst(f["timestamp"])
    hist = raw.get("fear_and_greed_historical", {}).get("data", [])
    days = {}
    for p in hist:
        d = kst(p["x"]).strftime("%Y-%m-%d")
        days[d] = round(float(p["y"]), 2)
    data = {
        "source": "https://edition.cnn.com/markets/fear-and-greed",
        "score": round(float(f["score"]), 2),
        "value": int(round(float(f["score"]))),
        "rating": f.get("rating", ""),
        "rating_ko": KO.get(f.get("rating", ""), f.get("rating", "")),
        "updated": t.strftime("%Y-%m-%dT%H:%M+09:00"),
        "updated_label": t.strftime("%m/%d %H:%M"),
        "previous_close": round(float(f["previous_close"]), 2),
        "previous_1_week": round(float(f["previous_1_week"]), 2),
        "previous_1_month": round(float(f["previous_1_month"]), 2),
        "previous_1_year": round(float(f["previous_1_year"]), 2),
        "parts": [{"key": k, "name": n, "score": round(float(raw[k]["score"]), 1), "rating_ko": KO.get(raw[k].get("rating", ""), raw[k].get("rating", ""))}
                  for k, n in PARTS if k in raw and raw[k].get("score") is not None],
        "recent": [{"date": d, "value": v} for d, v in sorted(days.items())[-10:]],
        "fetched": datetime.now(KST).strftime("%Y-%m-%dT%H:%M+09:00"),
    }
    try:
        old = json.load(open(out, encoding="utf-8"))
        if {k: v for k, v in old.items() if k != "fetched"} == {k: v for k, v in data.items() if k != "fetched"}:
            print("변화 없음", data["score"], data["updated"]); return
    except Exception:
        pass
    with open(out, "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=1)
    print("저장:", data["score"], data["rating"], data["updated"])


if __name__ == "__main__":
    main()
