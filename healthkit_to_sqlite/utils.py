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


def convert_xml_to_sqlite(fp, db, progress_callback=None, zipfile=None):
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
            workout_to_db(el, db, zipfile)
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


def workout_to_db(workout, db, zipfile=None):
    record = dict(workout.attrib)
    # add metadata entry items as extra keys
    for el in workout.findall("MetadataEntry"):
        record["metadata_" + el.attrib["key"]] = el.attrib["value"]
    # Dump any WorkoutEvent in a nested list for the moment
    record["workout_events"] = [el.attrib for el in workout.findall("WorkoutEvent")]
    pk = db["workouts"].insert(record, alter=True, hash_id="id").last_pk
    # Handle embedded WorkoutRoute/Location points
    points = [
        # <Location
        #   date="2016-11-14 07:25:44 -0700"
        #   latitude="37.7777"
        #   longitude="-122.426"
        #   altitude="21.2694"
        #   horizontalAccuracy="2.40948"
        #   verticalAccuracy="1.67859"
        #   course="-1"
        #   speed="2.48034" />
        el.attrib
        for el in workout.findall("WorkoutRoute/Location")
    ]
    # <FileReference path="/workout-routes/route_2019-06-11_3.00pm.gpx"/>
    fileref = workout.find(".//FileReference")
    if fileref is not None and zipfile is not None:
        path = fileref.attrib["path"]
        filename = path.split("/")[-1]
        for zip_filename in zipfile.filelist:
            if zip_filename.filename.endswith(filename):
                # Import points from this file
                points = list(points_from_gpx(zipfile.open(zip_filename).read()))

    # Convert points field to floats, except for date
    for point in points:
        point["workout_id"] = pk
        for key in point:
            if key not in ("date", "workout_id"):
                point[key] = float(point[key])

    db["workout_points"].insert_all(
        points, foreign_keys=[("workout_id", "workouts")], batch_size=50
    )


def points_from_gpx(gpx_xml):
    trkpts = ET.fromstring(gpx_xml).findall(
        "*//{http://www.topografix.com/GPX/1/1}trkpt"
    )
    for trkpt in trkpts:
        # <trkpt lat="37.781672" lon="-122.396397">
        #   <ele>4.076904</ele>
        #   <time>2019-06-11T22:00:42Z</time>
        #   <extensions>
        #     <speed>0.180883</speed>
        #     <course>206.252884</course>
        #     <hAcc>8.063116</hAcc>
        #     <vAcc>6.428697</vAcc>
        #   </extensions>
        # </trkpt>
        element_values = {
            e.tag.split("}")[-1]: e.text
            for e in trkpt.findall(".//*")
            if e.text is not None
        }
        # {'ele': '4.076904', 'time': '2019-06-11T22:00:42Z',
        #  'speed': '0.180883', 'course': '206.252884',
        #  'hAcc': '8.063116', 'vAcc': '6.428697'}
        # Now rename them to match WorkoutRoute/Location from above
        yield {
            "date": element_values["time"],
            "latitude": trkpt.attrib["lat"],
            "longitude": trkpt.attrib["lon"],
            "altitude": element_values["ele"],
            "horizontalAccuracy": element_values["hAcc"],
            "verticalAccuracy": element_values["vAcc"],
            "course": element_values["course"],
            "speed": element_values["speed"],
        }


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
