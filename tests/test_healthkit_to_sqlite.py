from click.testing import CliRunner
from healthkit_to_sqlite import cli, utils
import pytest
import pathlib


@pytest.fixture
def xml_fp():
    return open(pathlib.Path(__file__).parent / "export.xml", "r")


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
