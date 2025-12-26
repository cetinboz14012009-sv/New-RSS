import os
import hashlib
import datetime
import xml.etree.ElementTree as ET
from urllib.request import urlopen, Request
from xml.sax.saxutils import escape

# =====================
# AYARLAR
# =====================
OUT_FILE = os.path.join("feeds", "havuz.xml")
MAX_ITEMS = 50

SIGNATURE_HTML = "<br/><strong style='color:black;'>DB Haber Servisi</strong>"


def fetch(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (rss-bot)"})
    with urlopen(req, timeout=30) as r:
        return r.read()


def parse_rss(xml_bytes: bytes):
    """Sadece RSS 2.0 <channel><item>...</item> formatını okur."""
    try:
        root = ET.fromstring(xml_bytes)
    except Exception:
        return []

    channel = root.find("channel")
    if channel is None:
        return []

    items = []
    for item in channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        guid = (item.findtext("guid") or "").strip() or link or title

        if title and link:
            items.append(
                {"title": title, "link": link, "pubDate": pub, "guid": guid}
            )
    return items


def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()


def build_rss_xml(items):
    """RSS çıktısını string olarak üretir (description içinde CDATA ile HTML korunur)."""
    now = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

    parts = []
    parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    parts.append('<rss version="2.0">')
    parts.append("<channel>")
    parts.append("<title>Demokratik Birlik - Havuz</title>")
    parts.append("<link>https://cetinboz14012009-sv.github.io/New-RSS/</link>")
    parts.append("<description>Kaynaklardan otomatik toplanan ham haber havuzu</description>")
    parts.append("<language>tr</language>")
    parts.append(f"<lastBuildDate>{escape(now)}</lastBuildDate>")

    for it in items[:MAX_ITEMS]:
        title = escape(it["title"])
        link = escape(it["link"])
        guid = sha1(it["guid"])
        pub = escape(it["pubDate"]) if it["pubDate"] else ""

        # Description: CDATA içinde HTML (br + siyah kalın imza)
        desc_html = "Ham haber – düzenlenecek" + SIGNATURE_HTML

        parts.append("<item>")
        parts.append(f"<title>{title}</title>")
        parts.append(f"<link>{link}</link>")
        parts.append(f"<guid>{guid}</guid>")
        if pub:
            parts.append(f"<pubDate>{pub}</pubDate>")
        parts.append(f"<![CDATA[{desc_html}]]>".replace("<![CDATA[", "<description><![CDATA[").replace("]]>", "]]></description>"))
        parts.append("</item>")

    parts.append("</channel>")
    parts.append("</rss>")

    return "\n".join(parts)


def main():
    os.makedirs("feeds", exist_ok=True)

    with open(os.path.join("src", "sources.txt"), "r", encoding="utf-8") as f:
        urls = [x.strip() for x in f if x.strip() and not x.strip().startswith("#")]

    all_items = []
    for u in urls:
        try:
            all_items.extend(parse_rss(fetch(u)))
        except Exception as e:
            print("FAIL:", u, e)

    # Duplicate temizliği (link üzerinden)
    seen = set()
    unique = []
    for it in all_items:
        if it["link"] in seen:
            continue
        seen.add(it["link"])
        unique.append(it)

    xml_out = build_rss_xml(unique)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(xml_out)

    print("updated:", OUT_FILE)
    print("sources:", len(urls), "raw_items:", len(all_items), "unique_items:", len(unique))


if __name__ == "__main__":
    main()
