import os
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.i-boss.co.kr"
TARGET_URL = "https://www.i-boss.co.kr/ab-1957"
KEYWORDS = ["인플루언서", "시딩", "체험단"]
EXCLUDE = "[마감]"

SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": BASE_URL,
}


def fetch_listings():
    resp = requests.get(TARGET_URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")

    results = []

    for a in soup.find_all("a", href=True):
        title = a.get_text(strip=True)
        if not title:
            continue
        if EXCLUDE in title:
            continue
        if not any(kw in title for kw in KEYWORDS):
            continue

        href = a["href"]
        if not href.startswith("/ab-1958-"):
            continue
        link = BASE_URL + href

        if any(r["link"] == link for r in results):
            continue

        results.append({"title": title, "link": link})

    return results


def send_to_slack(listings):
    if not listings:
        payload = {"text": "오늘은 새로운 공고가 안보이네요. 왈왈"}
        requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10).raise_for_status()
        print("새로운 공고 없음")
        return
    header = f"*[i-boss] 오늘의 공고 {len(listings)}개*"
    lines = [header]
    for i, item in enumerate(listings, 1):
        title = item['title'][:40] + "..." if len(item['title']) > 40 else item['title']
        lines.append(f"{i}. <{item['link']}|{title}>")
    payload = {"text": "\n".join(lines)}
    resp = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
    resp.raise_for_status()
    print(f"슬랙 전송 완료: {len(listings)}건")


if __name__ == "__main__":
    try:
        listings = fetch_listings()
    except requests.exceptions.ConnectTimeout:
        print("연결 타임아웃: i-boss.co.kr에 접근할 수 없습니다. (GitHub Actions IP 차단 가능성)")
        payload = {"text": ":warning: i-boss 크롤링 실패: 사이트 연결 타임아웃 (GitHub Actions IP 차단)"}
        requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10).raise_for_status()
        raise SystemExit(0)
    except requests.exceptions.ConnectionError as e:
        print(f"연결 오류: {e}")
        payload = {"text": f":warning: i-boss 크롤링 실패: 연결 오류 - {e}"}
        requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10).raise_for_status()
        raise SystemExit(0)
    print(f"수집된 공고: {len(listings)}건")
    for item in listings:
        print(f"  - {item['title']}")
    send_to_slack(listings)
