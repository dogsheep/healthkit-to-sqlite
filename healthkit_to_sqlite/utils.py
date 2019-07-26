from xml.etree import ElementTree as ET


def find_all_tags(fp, tags, progress_callback=None):
    parser = ET.XMLPullParser(("start", "end"))
    root = None
    while True:
        chunk = fp.read(1024 * 1024)
        if not chunk:
            break
        parser.feed(chunk)
        for event, el in parser.read_events():
            if event == "start" and root is None:
                root = el
            if event == "end" and el.tag in tags:
                yield el.tag, el
            root.clear()
        if progress_callback is not None:
            progress_callback(len(chunk))


def convert_xml_to_sqlite(fp, db, progress_callback=None):
    activity_summaries = []
    records = []
    for tag, el in find_all_tags(
        fp, {"Record", "Workout", "ActivitySummary"}, progress_callback
    ):
        if tag == "ActivitySummary":
            activity_summaries.append(dict(el.attrib))
            if len(activity_summaries) >= 100:
                db["activity_summary"].insert_all(activity_summaries)
                activity_summaries = []
        elif tag == "Workout":
            workout_to_db(el, db)
        elif tag == "Record":
            record = dict(el.attrib)
            for child in el.findall("MetadataEntry"):
                record["metadata_" + child.attrib["key"]] = child.attrib["value"]
            records.append(record)
            if len(records) >= 200:
                write_records(records, db)
                records = []
        el.clear()
    if records:
        write_records(records, db)
    if activity_summaries:
        db["activity_summary"].insert_all(activity_summaries)


def workout_to_db(workout, db):
    record = dict(workout.attrib)
    # add metadata entry items as extra keys
    for el in workout.findall("MetadataEntry"):
        record["metadata_" + el.attrib["key"]] = el.attrib["value"]
    # Dump any WorkoutEvent in a nested list for the moment
    record["workout_events"] = [el.attrib for el in workout.findall("WorkoutEvent")]
    pk = db["workouts"].insert(record, alter=True, hash_id="id").last_pk
    points = [
        dict(el.attrib, workout_id=pk)
        for el in workout.findall("WorkoutRoute/Location")
    ]
    db["workout_points"].insert_all(
        points, foreign_keys=[("workout_id", "workouts")], batch_size=50
    )


def write_records(records, db):
    # We write records into tables based on their types
    records_by_type = {}
    for record in records:
        table = "r{}".format(
            record.pop("type")
            .replace("HKQuantityTypeIdentifier", "")
            .replace("HKCategoryTypeIdentifier", "")
        )
        records_by_type.setdefault(table, []).append(record)
    # Bulk inserts for each one
    for table, records_for_table in records_by_type.items():
        db[table].insert_all(
            records_for_table,
            alter=True,
            column_order=["startDate", "endDate", "value", "unit"],
            batch_size=50,
        )
