import os, hashlib, datetime
import xml.etree.ElementTree as ET
from urllib.request import urlopen, Request
from email.utils import parsedate_to_datetime

MAX_ITEMS = 30
OUT_FILE = os.path.join("feeds", "politika.xml")

def fetch(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "news-rss-bot/1.0"})
    with urlopen(req, timeout=30) as r:
        return r.read()

def text(el, default=""):
    return el.text.strip() if el is not None and el.text else default

def parse_rss(xml_bytes):
    root = ET.fromstring(xml_bytes)
    channel = root.find("channel")
    if channel is None:
        return []

    items = []
    for item in channel.findall("item"):
        title = text(item.find("title"))
        link = text(item.find("link"))
        pub = text(item.find("pubDate"))
        guid = text(item.find("guid")) or link or title

        if title and link:
            items.append({
                "title": title,
                "link": link,
                "pubDate": pub,
                "guid": guid
            })
    return items

def parse_date(pub):
    try:
        d = parsedate_to_datetime(pub)
        if d.tzinfo is None:
            d = d.replace(tzinfo=datetime.timezone.utc)
        return d
    except:
        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)

def build(items):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "Demokratik Birlik - Politika"
    ET.SubElement(channel, "link").text = "https://cetinboz14012009-sv.github.io/New-RSS/"
    ET.SubElement(channel, "description").text = "Otomatik haber havuzu (son 30 haber)"
    ET.SubElement(channel, "language").text = "tr"
    ET.SubElement(channel, "lastBuildDate").text = datetime.datetime.utcnow().strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )

    for item in items[:MAX_ITEMS]:
        i = ET.SubElement(channel, "item")
        ET.SubElement(i, "title").text = item["title"]
        ET.SubElement(i, "link").text = item["link"]
        ET.SubElement(i, "guid").text = hashlib.sha1(item["guid"].encode()).hexdigest()
        if item["pubDate"]:
            ET.SubElement(i, "pubDate").text = item["pubDate"]
        ET.SubElement(i, "description").text = "Ham haber – editör onayı bekliyor."

    return ET.tostring(rss, encoding="utf-8", xml_declaration=True).decode("utf-8")

def main():
    os.makedirs("feeds", exist_ok=True)

    with open("src/sources.txt", "r", encoding="utf-8") as f:
        sources = [s.strip() for s in f if s.strip()]

    all_items = []
    for src in sources:
        try:
            all_items.extend(parse_rss(fetch(src)))
        except Exception as e:
            print("Hata:", src, e)

    # tekrarları temizle
    seen = set()
    unique = []
    for i in all_items:
        if i["link"] not in seen:
            seen.add(i["link"])
            unique.append(i)

    # EN YENİLER EN ÜSTTE
    unique.sort(key=lambda x: parse_date(x.get("pubDate")), reverse=True)

    xml = build(unique)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(xml)

    print("RSS güncellendi:", OUT_FILE)


if __name__ == "__main__":
    main()
