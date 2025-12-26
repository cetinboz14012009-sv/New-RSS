import os
import xml.etree.ElementTree as ET

MAX_ITEMS = 30
FILE = "feeds/politika.xml"

def main():
    # Dosya yoksa workflow'u bozma
    if not os.path.exists(FILE):
        print(f"[trim] {FILE} not found, skipping.")
        return

    try:
        tree = ET.parse(FILE)
        root = tree.getroot()
        channel = root.find("channel")

        if channel is None:
            print("[trim] <channel> not found, skipping.")
            return

        items = channel.findall("item")

        # En yeni 30 kalsın (RSS'te üstte olanlar daha yeni varsayılır)
        for item in items[MAX_ITEMS:]:
            channel.remove(item)

        tree.write(FILE, encoding="utf-8", xml_declaration=True)
        print(f"[trim] trimmed to {min(len(items), MAX_ITEMS)} items.")

    except Exception as e:
        # XML bozuksa workflow'u bozma
        print("[trim] parse error, skipping:", e)

if __name__ == "__main__":
    main()
