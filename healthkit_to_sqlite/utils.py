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


def convert_xml_to_sqlite(fp, db):
    activity_summaries = []
    for tag, el in find_all_tags(fp, {"Record", "Workout", "ActivitySummary"}):
        if tag == "ActivitySummary":
            activity_summaries.append(dict(el.attrib))
    db["activity_summary"].upsert_all(activity_summaries, hash_id="id")
