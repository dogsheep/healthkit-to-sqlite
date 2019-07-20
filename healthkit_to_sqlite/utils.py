from xml.etree import ElementTree as ET


def find_all_tags(fp, tags):
    parser = ET.XMLPullParser(["end"])
    while True:
        chunk = fp.read(1024 * 1024 * 8)
        if not chunk:
            break
        parser.feed(chunk)
        for _, el in parser.read_events():
            if el.tag in tags:
                yield el.tag, el
