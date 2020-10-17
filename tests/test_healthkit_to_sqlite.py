from click.testing import CliRunner
from healthkit_to_sqlite import cli, utils
import io
import pathlib
import pytest
import sqlite_utils
from sqlite_utils.db import ForeignKey
import pathlib
import zipfile


@pytest.fixture
def xml_path():
    return pathlib.Path(__file__).parent / "export.xml"


@pytest.fixture
def xml_fp(xml_path):
    return open(xml_path, "r")


@pytest.fixture
def converted(xml_fp):
    db = sqlite_utils.Database(":memory:")
    utils.convert_xml_to_sqlite(xml_fp, db)
    return db


@pytest.fixture(params=["export.xml", "exportar.xml"])
def zip_file_with_gpx(request, tmpdir):
    export_xml_filename = request.param
    zip_contents_path = pathlib.Path(__file__).parent / "zip_contents"
    archive = str(tmpdir / "export.zip")
    buf = io.BytesIO()
    zf = zipfile.ZipFile(buf, "w")
    for filepath in zip_contents_path.glob("**/*"):
        if filepath.is_file():
            arcname = filepath.relative_to(zip_contents_path)
            if arcname.name == "export.xml":
                arcname = arcname.parent / export_xml_filename
            zf.write(filepath, str(arcname))
    zf.close()
    with open(archive, "wb") as fp:
        fp.write(buf.getbuffer())
    return tmpdir, archive


def test_help():
    result = CliRunner().invoke(cli.cli, ["--help"])
    assert result.output.startswith("Usage: cli")


def test_fixture(xml_fp):
    assert xml_fp.read().startswith("<Health")


def test_find_all_tags(xml_fp):
    findings = list(
        utils.find_all_tags(xml_fp, {"Record", "Workout", "ActivitySummary"})
    )
    assert ["Record", "Record", "Workout", "ActivitySummary", "ActivitySummary"] == [
        f[0] for f in findings
    ]


def test_converted_activity_summaries(converted):
    actual = list(converted["activity_summary"].rows)
    assert [
        {
            "dateComponents": "2016-11-15",
            "activeEnergyBurned": "590.252",
            "activeEnergyBurnedGoal": "630",
            "activeEnergyBurnedUnit": "kcal",
            "appleExerciseTime": "68",
            "appleExerciseTimeGoal": "30",
            "appleStandHours": "13",
            "appleStandHoursGoal": "12",
        },
        {
            "dateComponents": "2016-11-16",
            "activeEnergyBurned": "323.513",
            "activeEnergyBurnedGoal": "630",
            "activeEnergyBurnedUnit": "kcal",
            "appleExerciseTime": "39",
            "appleExerciseTimeGoal": "30",
            "appleStandHours": "9",
            "appleStandHoursGoal": "12",
        },
    ] == actual


def test_converted_workouts(converted):
    actual = list(converted["workouts"].rows)
    assert [
        {
            "id": "e615a9651eab4d95debed14c2c2f7cce0c31feed",
            "workoutActivityType": "HKWorkoutActivityTypeRunning",
            "duration": "5.19412346680959",
            "durationUnit": "min",
            "totalDistance": "0.4971749504535062",
            "totalDistanceUnit": "mi",
            "totalEnergyBurned": "48.74499999999999",
            "totalEnergyBurnedUnit": "kcal",
            "sourceName": "Apple\xa0Watch",
            "sourceVersion": "3.1",
            "creationDate": "2016-11-14 07:33:49 -0700",
            "startDate": "2016-11-14 07:25:41 -0700",
            "endDate": "2016-11-14 07:30:52 -0700",
            "metadata_HKTimeZone": "America/Los_Angeles",
            "metadata_HKWeatherTemperature": "56 degF",
            "metadata_HKWeatherHumidity": "96 %",
            "workout_events": "[]",
        }
    ] == actual
    assert [
        ForeignKey(
            table="workout_points",
            column="workout_id",
            other_table="workouts",
            other_column="id",
        )
    ] == converted["workout_points"].foreign_keys
    actual_points = list(converted["workout_points"].rows)
    assert [
        {
            "date": "2016-11-14 07:25:44 -0700",
            "latitude": 37.7777,
            "longitude": -122.426,
            "altitude": 21.2694,
            "horizontalAccuracy": 2.40948,
            "verticalAccuracy": 1.67859,
            "course": -1.0,
            "speed": 2.48034,
            "workout_id": "e615a9651eab4d95debed14c2c2f7cce0c31feed",
        },
        {
            "date": "2016-11-14 07:25:44 -0700",
            "latitude": 37.7777,
            "longitude": -122.426,
            "altitude": 21.2677,
            "horizontalAccuracy": 2.40059,
            "verticalAccuracy": 1.67236,
            "course": -1.0,
            "speed": 2.48034,
            "workout_id": "e615a9651eab4d95debed14c2c2f7cce0c31feed",
        },
    ] == actual_points


def test_converted_records(converted):
    # These should have been recorded in rBodyMassIndex and rHeartRate
    body_mass_actual = list(converted["rBodyMassIndex"].rows)
    assert [
        {
            "sourceName": "Health Mate",
            "sourceVersion": "2160040",
            "unit": "count",
            "creationDate": "2016-11-20 17:57:19 -0700",
            "startDate": "2016-04-18 08:25:32 -0700",
            "endDate": "2016-04-18 08:25:32 -0700",
            "value": "22.5312",
            "metadata_Health Mate App Version": "2.16.0",
            "metadata_Withings User Identifier": "12345",
            "metadata_Modified Date": "2016-04-18 15:56:05 +0000",
            "metadata_Withings Link": "withings-bd2://timeline/measure?userid=12345&date=482685932&type=1",
            "metadata_HKWasUserEntered": "0",
        }
    ] == body_mass_actual
    heart_rate_actual = list(converted["rHeartRate"].rows)
    assert [
        {
            "sourceName": "Apple\xa0Watch",
            "sourceVersion": "4.3.1",
            "unit": "count/min",
            "creationDate": "2018-09-10 02:47:35 -0700",
            "startDate": "2018-09-10 02:28:55 -0700",
            "endDate": "2018-09-10 02:28:55 -0700",
            "value": "72",
            "device": "<<HKDevice: 0x282a45810>, name:Apple Watch, manufacturer:Apple, model:Watch, hardware:Watch2,4, software:4.3.1>",
            "metadata_HKMetadataKeyHeartRateMotionContext": "0",
        }
    ] == heart_rate_actual


def test_cli_rejects_non_zip(xml_path, tmpdir):
    result = CliRunner().invoke(cli.cli, [str(xml_path), str(tmpdir / "output.db")])
    assert 1 == result.exit_code
    assert (
        "Error: File is not a zip file. Use --xml if you are "
        "running against an XML file."
    ) == result.output.strip()


def test_cli_parses_xml_file(xml_path, tmpdir):
    output = str(tmpdir / "output.db")
    result = CliRunner().invoke(cli.cli, [str(xml_path), output, "--xml"])
    assert 0 == result.exit_code
    db = sqlite_utils.Database(output)
    assert {
        "workouts",
        "workout_points",
        "activity_summary",
        "rHeartRate",
        "rBodyMassIndex",
    } == set(db.table_names())


def test_zip_file_with_gpx(zip_file_with_gpx):
    tmpdir, export = zip_file_with_gpx
    output = str(tmpdir / "output.db")
    result = CliRunner().invoke(cli.cli, [export, output])
    assert result.exit_code == 0, result.output
    db = sqlite_utils.Database(output)
    assert {
        "workouts",
        "workout_points",
        "activity_summary",
        "rHeartRate",
        "rBodyMassIndex",
    } == set(db.table_names())
    # Confirm workout points from GPX were correctly imported
    assert [
        {
            "date": "2019-06-11T22:00:42Z",
            "latitude": 37.781672,
            "longitude": -122.396397,
            "altitude": 4.076904,
            "horizontalAccuracy": 8.063116,
            "verticalAccuracy": 6.428697,
            "course": 206.252884,
            "speed": 0.180883,
            "workout_id": "e615a9651eab4d95debed14c2c2f7cce0c31feed",
        },
        {
            "date": "2019-06-11T22:00:42Z",
            "latitude": 37.78167,
            "longitude": -122.396396,
            "altitude": 4.083609,
            "horizontalAccuracy": 8.29291,
            "verticalAccuracy": 6.481525,
            "course": 206.252884,
            "speed": 0.116181,
            "workout_id": "e615a9651eab4d95debed14c2c2f7cce0c31feed",
        },
        {
            "date": "2019-06-11T22:00:43Z",
            "latitude": 37.78167,
            "longitude": -122.396394,
            "altitude": 4.085232,
            "horizontalAccuracy": 8.453521,
            "verticalAccuracy": 6.549587,
            "course": 206.252884,
            "speed": 0.054395,
            "workout_id": "e615a9651eab4d95debed14c2c2f7cce0c31feed",
        },
    ] == list(db["workout_points"].rows)
