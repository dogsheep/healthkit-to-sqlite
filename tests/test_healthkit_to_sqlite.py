from click.testing import CliRunner
from healthkit_to_sqlite import cli, utils
import pytest
import sqlite_utils
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
