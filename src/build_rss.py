import os, hashlib, datetime
import xml.etree.ElementTree as ET
from urllib.request import urlopen, Request
from email.utils import parsedate_to_datetime

MAX_ITEMS = 30
MAX_AGE_HOURS = 48
OUT_FILE = os.path.join("feeds", "havuz.xml")

def fetch(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "news-rss-bot/1.0"})
    with urlopen(req, timeout=30) as r:
        return r.read()

def text(el, default=""):
    return el.text.strip() if el is not None and el.text else default

def parse_date(pub: str):
    try:
        dt = parsedate_to_datetime(pub)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except Exception:
        return None

def parse_rss(xml_bytes):
    root = ET.fromstring(xml_bytes)
    channel = root.find("channel")
    if channel is None:
        return []

    out = []
    for item in channel.findall("item"):
        title = text(item.find("title"))
        link = text(item.find("link"))
        pub = text(item.find("pubDate"))
        guid = text(item.find("guid")) or link or title

        if not (title and link):
            continue

        dt = parse_date(pub)
        out.append({
            "title": title,
            "link": link,
            "pubDate": pub,
            "guid": guid,
            "dt": dt,
        })
    return out

def guid_hash(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()

def build(items):
    rss = ET.Element("rss", version="2.0")
    ch = ET.SubElement(rss, "channel")

    ET.SubElement(ch, "title").text = "Demokratik Birlik - Haber Havuzu (Son 30 / Son 48 Saat)"
    ET.SubElement(ch, "link").text = "https://cetinboz14012009-sv.github.io/New-RSS/"
    ET.SubElement(ch, "description").text = "Kaynaklardan toplanan ham haber havuzu (editör seçimi için)."
    ET.SubElement(ch, "language").text = "tr"
    ET.SubElement(ch, "lastBuildDate").text = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

    for it in items[:MAX_ITEMS]:
        i = ET.SubElement(ch, "item")
        ET.SubElement(i, "title").text = it["title"]
        ET.SubElement(i, "link").text = it["link"]
        ET.SubElement(i, "guid").text = guid_hash(it["guid"])
        if it.get("pubDate"):
            ET.SubElement(i, "pubDate").text = it["pubDate"]
        ET.SubElement(i, "description").text = "Ham haber – editör onayı bekliyor."

    return ET.tostring(rss, encoding="utf-8", xml_declaration=True).decode("utf-8")

def main():
    os.makedirs("feeds", exist_ok=True)

    with open("src/sources.txt", "r", encoding="utf-8") as f:
        sources = [s.strip() for s in f if s.strip() and not s.strip().startswith("#")]

    all_items = []
    for src in sources:
        try:
            all_items.extend(parse_rss(fetch(src)))
        except Exception as e:
            print("Hata:", src, e)

    # duplicate temizliği (link bazlı)
    seen = set()
    unique = []
    for it in all_items:
        if it["link"] in seen:
            continue
        seen.add(it["link"])
        unique.append(it)

    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff = now - datetime.timedelta(hours=MAX_AGE_HOURS)

    # sadece taze + pubDate'i olanlar
    fresh = [it for it in unique if it["dt"] is not None and it["dt"] >= cutoff]

    # en yeni en üstte
    fresh.sort(key=lambda x: x["dt"], reverse=True)

    xml = build(fresh)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(xml)

    print("RSS güncellendi:", OUT_FILE, "items:", len(fresh))

if __name__ == "__main__":
    main()
