from click.testing import CliRunner
from healthkit_to_sqlite import cli


def test_help():
    result = CliRunner().invoke(cli.cli, ["--help"])
    assert result.output.startswith("Usage: cli")
