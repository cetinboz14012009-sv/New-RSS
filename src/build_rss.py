import os, hashlib, datetime
import xml.etree.ElementTree as ET
from urllib.request import urlopen, Request

MAX_ITEMS = 30
OUT_FILE = os.path.join("feeds", "politika.xml")

def fetch(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "news-rss-bot/1.0"})
    with urlopen(req, timeout=30) as r:
        return r.read()

def t(el, default=""):
    return el.text.strip() if el is not None and el.text else default

def parse_rss(xml_bytes: bytes):
    root = ET.fromstring(xml_bytes)
    channel = root.find("channel")
    if channel is None:
        return []
    out = []
    for item in channel.findall("item"):
        title = t(item.find("title"))
        link = t(item.find("link"))
        pub = t(item.find("pubDate"))
        guid = t(item.find("guid")) or link or title
        if title and link:
            out.append({"title": title, "link": link, "pubDate": pub, "guid": guid})
    return out

def guid_hash(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()

def build(items):
    rss = ET.Element("rss", version="2.0")
    ch = ET.SubElement(rss, "channel")

    ET.SubElement(ch, "title").text = "Demokratik Birlik - Politika (Havuz)"
    ET.SubElement(ch, "link").text = "https://cetinboz14012009-sv.github.io/New-RSS/"
    ET.SubElement(ch, "description").text = "Kaynaklardan toplanan haber havuzu (taslak)."
    ET.SubElement(ch, "language").text = "tr"
    ET.SubElement(ch, "lastBuildDate").text = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

    for it in items[:MAX_ITEMS]:
        i = ET.SubElement(ch, "item")
        ET.SubElement(i, "title").text = it["title"]
        ET.SubElement(i, "link").text = it["link"]
        ET.SubElement(i, "guid").text = guid_hash(it["guid"])
        if it["pubDate"]:
            ET.SubElement(i, "pubDate").text = it["pubDate"]
        ET.SubElement(i, "description").text = "Ham havuz. (AI özet/çeviri bir sonraki aşamada eklenecek.)"

    return ET.tostring(rss, encoding="utf-8", xml_declaration=True).decode("utf-8")

def main():
    os.makedirs("feeds", exist_ok=True)

    with open(os.path.join("src", "sources.txt"), "r", encoding="utf-8") as f:
        urls = [x.strip() for x in f if x.strip() and not x.strip().startswith("#")]

    all_items = []
    for u in urls:
        try:
            all_items.extend(parse_rss(fetch(u)))
        except Exception as e:
            print("FAIL", u, e)

    # duplicate temizliği
    seen = set()
    unique = []
    for it in all_items:
        if it["link"] in seen:
            continue
        seen.add(it["link"])
        unique.append(it)

    xml_out = build(unique)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(xml_out)

    print("updated:", OUT_FILE)

if __name__ == "__main__":
    main()
