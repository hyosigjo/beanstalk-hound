import os
import re
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.i-boss.co.kr"
TARGET_URL = (
    "https://www.i-boss.co.kr/insiter.php"
    "?design_file=1957.php&search_value=%EC%9D%B8%ED%94%8C%EB%A3%A8%EC%96%B8%EC%84%9C"
)
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
    resp.encoding = resp.apparent_encoding
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
        if href.startswith("http"):
            link = href
        elif href.startswith("/"):
            link = BASE_URL + href
        else:
            continue

        if any(r["link"] == link for r in results):
            continue

        results.append({"title": title, "link": link})

    return results


def send_to_slack(listings):
    if not listings:
        print("새로운 공고 없음")
        return

    lines = ["*[i-boss 대행게시판] 오늘의 인플루언서/시딩/체험단 공고*\n"]
    for item in listings:
        lines.append(f"• <{item['link']}|{item['title']}>")

    payload = {"text": "\n".join(lines)}
    resp = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
    resp.raise_for_status()
    print(f"슬랙 전송 완료: {len(listings)}건")


if __name__ == "__main__":
    listings = fetch_listings()
    print(f"수집된 공고: {len(listings)}건")
    for item in listings:
        print(f"  - {item['title']}")
    send_to_slack(listings)