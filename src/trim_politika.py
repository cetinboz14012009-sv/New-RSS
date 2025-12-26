import xml.etree.ElementTree as ET

MAX_ITEMS = 30
FILE = "feeds/politika.xml"

tree = ET.parse(FILE)
root = tree.getroot()
channel = root.find("channel")

items = channel.findall("item")

# En eski haberleri sil (en yeni 30 kalsın)
for item in items[MAX_ITEMS:]:
    channel.remove(item)

tree.write(FILE, encoding="utf-8", xml_declaration=True)

