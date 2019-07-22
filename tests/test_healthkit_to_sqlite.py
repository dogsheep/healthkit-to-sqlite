from click.testing import CliRunner
from healthkit_to_sqlite import cli, utils
import pytest
import sqlite_utils
from sqlite_utils.db import ForeignKey
import pathlib


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
            "latitude": "37.7777",
            "longitude": "-122.426",
            "altitude": "21.2694",
            "horizontalAccuracy": "2.40948",
            "verticalAccuracy": "1.67859",
            "course": "-1",
            "speed": "2.48034",
            "workout_id": "e615a9651eab4d95debed14c2c2f7cce0c31feed",
        },
        {
            "date": "2016-11-14 07:25:44 -0700",
            "latitude": "37.7777",
            "longitude": "-122.426",
            "altitude": "21.2677",
            "horizontalAccuracy": "2.40059",
            "verticalAccuracy": "1.67236",
            "course": "-1",
            "speed": "2.48034",
            "workout_id": "e615a9651eab4d95debed14c2c2f7cce0c31feed",
        },
    ] == actual_points


def test_converted_records(converted):
    actual = list(converted["records"].rows)
    assert [
        {
            "type": "HKQuantityTypeIdentifierBodyMassIndex",
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
            "device": None,
            "metadata_HKMetadataKeyHeartRateMotionContext": None,
        },
        {
            "type": "HKQuantityTypeIdentifierHeartRate",
            "sourceName": "Apple\xa0Watch",
            "sourceVersion": "4.3.1",
            "unit": "count/min",
            "creationDate": "2018-09-10 02:47:35 -0700",
            "startDate": "2018-09-10 02:28:55 -0700",
            "endDate": "2018-09-10 02:28:55 -0700",
            "value": "72",
            "metadata_Health Mate App Version": None,
            "metadata_Withings User Identifier": None,
            "metadata_Modified Date": None,
            "metadata_Withings Link": None,
            "metadata_HKWasUserEntered": None,
            "device": "<<HKDevice: 0x282a45810>, name:Apple Watch, manufacturer:Apple, model:Watch, hardware:Watch2,4, software:4.3.1>",
            "metadata_HKMetadataKeyHeartRateMotionContext": "0",
        },
    ] == actual


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
    assert [
        "workouts",
        "workout_points",
        "records",
        "activity_summary",
    ] == db.table_names()
