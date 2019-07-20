from click.testing import CliRunner
from healthkit_to_sqlite import cli, utils
import pytest
import sqlite_utils
from sqlite_utils.db import ForeignKey
import pathlib


@pytest.fixture
def xml_fp():
    return open(pathlib.Path(__file__).parent / "export.xml", "r")


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
    assert [
        {
            "id": "f0801853ea483cb3b80f923abdffefdd9427a940",
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
            "id": "5aeb50d13bf455c2485ad008177c3f105949dee1",
            "dateComponents": "2016-11-16",
            "activeEnergyBurned": "323.513",
            "activeEnergyBurnedGoal": "630",
            "activeEnergyBurnedUnit": "kcal",
            "appleExerciseTime": "39",
            "appleExerciseTimeGoal": "30",
            "appleStandHours": "9",
            "appleStandHoursGoal": "12",
        },
    ] == list(converted["activity_summary"].rows)


def test_converted_workouts(converted):
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
    ] == list(converted["workouts"].rows)
    assert [
        ForeignKey(
            table="workout_points",
            column="workout_id",
            other_table="workouts",
            other_column="id",
        )
    ] == converted["workout_points"].foreign_keys
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
    ] == list(converted["workout_points"].rows)
