"""미래에셋증권 시황 텔레그램(t.me/globalmktinsight) 최신 글을 telegram.json으로 저장.
GitHub Actions에서 15분마다 실행. 표준 라이브러리만 사용."""
import html, json, re, sys, urllib.request
from datetime import datetime, timezone, timedelta

CH = "globalmktinsight"
KST = timezone(timedelta(hours=9))
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ko,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def clean(fragment):
    t = re.sub(r"<br\s*/?>", "\n", fragment)
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t).replace(" ", " ")
    lines = [re.sub(r"[ \t]+", " ", l).strip() for l in t.split("\n")]
    return "\n".join(l for l in lines if l)


def parse(page):
    posts = []
    for chunk in re.split(r'(?=<div class="tgme_widget_message_wrap)', page)[1:]:
        m = re.search(r'data-post="%s/(\d+)"' % CH, chunk)
        if not m:
            continue
        pid = int(m.group(1))
        tm = re.search(r'<time datetime="([^"]+)"', chunk)
        tx = re.search(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', chunk, re.S)
        if not tm or not tx:
            continue  # 고정 알림 등 서비스 메시지
        text = clean(tx.group(1))
        if not text:
            continue
        fw = re.search(r'tgme_widget_message_forwarded_from_name[^>]*>(?:<span[^>]*>)?([^<]+)', chunk)
        when = datetime.fromisoformat(tm.group(1)).astimezone(KST)
        lines = text.split("\n")
        title = lines[0][:80]
        rest = " ".join(lines[1:])
        excerpt = (rest[:150] + "…") if len(rest) > 150 else rest
        posts.append({
            "id": pid,
            "time": when.strftime("%Y-%m-%dT%H:%M+09:00"),
            "label": when.strftime("%m/%d %H:%M"),
            "title": title,
            "excerpt": excerpt,
            "fwd": html.unescape(fw.group(1).strip()) if fw else None,
            "url": "https://t.me/%s/%d" % (CH, pid),
        })
    return posts


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "telegram.json"
    page = get("https://t.me/s/%s" % CH)
    posts = {p["id"]: p for p in parse(page)}
    if len(posts) < 8 and posts:  # 첫 페이지가 짧으면 한 페이지 더
        page2 = get("https://t.me/s/%s?before=%d" % (CH, min(posts)))
        for p in parse(page2):
            posts.setdefault(p["id"], p)
    if not posts:
        sys.exit("게시물을 찾지 못함")
    items = sorted(posts.values(), key=lambda p: p["id"], reverse=True)[:12]
    try:
        old = json.load(open(out, encoding="utf-8"))
        if [p["id"] for p in old.get("posts", [])] == [p["id"] for p in items] and old.get("posts") == items:
            print("변화 없음"); return
    except Exception:
        pass
    data = {
        "channel": CH,
        "channel_url": "https://t.me/%s" % CH,
        "updated": datetime.now(KST).strftime("%Y-%m-%dT%H:%M+09:00"),
        "posts": items,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("저장:", len(items), "개, 최신", items[0]["id"])


if __name__ == "__main__":
    main()
