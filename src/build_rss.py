import os
import hashlib
import datetime
import xml.etree.ElementTree as ET
from urllib.request import urlopen, Request


# =====================
# AYARLAR
# =====================
OUT_FILE = os.path.join("feeds", "havuz.xml")
MAX_ITEMS = 50


# =====================
# YARDIMCI FONKSİYONLAR
# =====================
def fetch(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=30) as r:
        return r.read()


def parse_rss(xml_bytes: bytes):
    try:
        root = ET.fromstring(xml_bytes)
    except Exception:
        return []

    channel = root.find("channel")
    if channel is None:
        return []

    items = []
    for item in channel.findall("item"):
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        pub = item.findtext("pubDate", "").strip()
        guid = item.findtext("guid", "").strip() or link or title

        if title and link:
            items.append({
                "title": title,
                "link": link,
                "pubDate": pub,
                "guid": guid
            })

    return items


def build_feed(items):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "Demokratik Birlik - Havuz"
    ET.SubElement(channel, "link").text = "https://cetinboz14012009-sv.github.io/New-RSS/"
    ET.SubElement(channel, "description").text = "Kaynaklardan otomatik toplanan ham haber havuzu"
    ET.SubElement(channel, "language").text = "tr"
    ET.SubElement(channel, "lastBuildDate").text = datetime.datetime.utcnow().strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )

    for it in items[:MAX_ITEMS]:
        i = ET.SubElement(channel, "item")
        ET.SubElement(i, "title").text = it["title"]
        ET.SubElement(i, "link").text = it["link"]
        ET.SubElement(i, "guid").text = hashlib.sha1(it["guid"].encode()).hexdigest()
        if it["pubDate"]:
            ET.SubElement(i, "pubDate").text = it["pubDate"]
   ET.SubElement(i, "description").text = (
    "Ham haber – düzenlenecek"
    "<br/><strong style='color:black;'>DB Haber Servisi</strong>"
)


    return ET.tostring(rss, encoding="utf-8", xml_declaration=True).decode("utf-8")


# =====================
# ANA ÇALIŞMA
# =====================
def main():
    os.makedirs("feeds", exist_ok=True)

    with open(os.path.join("src", "sources.txt"), "r", encoding="utf-8") as f:
        urls = [x.strip() for x in f if x.strip() and not x.strip().startswith("#")]

    print("sources:", len(urls))

    all_items = []
    for u in urls:
        try:
            all_items.extend(parse_rss(fetch(u)))
        except Exception as e:
            print("FAIL:", u, e)

    print("raw_items:", len(all_items))

    # duplicate temizle
    seen = set()
    unique = []
    for it in all_items:
        if it["link"] in seen:
            continue
        seen.add(it["link"])
        unique.append(it)

    print("unique_items:", len(unique))

    xml_out = build_feed(unique)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(xml_out)


if __name__ == "__main__":
    main()

