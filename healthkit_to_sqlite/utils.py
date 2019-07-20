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
    records = []
    for tag, el in find_all_tags(fp, {"Record", "Workout", "ActivitySummary"}):
        if tag == "ActivitySummary":
            activity_summaries.append(dict(el.attrib))
        elif tag == "Workout":
            workout_to_db(el, db)
        elif tag == "Record":
            record = dict(el.attrib)
            for child in el.findall("MetadataEntry"):
                record["metadata_" + child.attrib["key"]] = child.attrib["value"]
            records.append(record)
            if len(records) >= 100:
                db["records"].insert_all(records, alter=True, hash_id="id")
                records = []
    if records:
        db["records"].insert_all(records, alter=True, hash_id="id")
    db["activity_summary"].upsert_all(activity_summaries, hash_id="id")


def workout_to_db(workout, db):
    record = dict(workout.attrib)
    # add metadata entry items as extra keys
    for el in workout.findall("MetadataEntry"):
        record["metadata_" + el.attrib["key"]] = el.attrib["value"]
    # Dump any WorkoutEvent in a nested list for the moment
    record["workout_events"] = [el.attrib for el in workout.findall("WorkoutEvent")]
    pk = db["workouts"].insert(record, hash_id="id", alter=True).last_pk
    points = [
        dict(el.attrib, workout_id=pk)
        for el in workout.findall("WorkoutRoute/Location")
    ]
    db["workout_points"].insert_all(points, foreign_keys=[("workout_id", "workouts")])
