import click
import zipfile
import sqlite_utils
from .utils import convert_xml_to_sqlite

EXPORT_XML = "apple_health_export/export.xml"


@click.command()
@click.argument(
    "export_zip",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
@click.argument(
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
def cli(export_zip, db_path):
    "Convert HealthKit file from exported zip file into a SQLite database"
    zf = zipfile.ZipFile(export_zip)
    # Ensure export.xml is in there
    filenames = {zi.filename for zi in zf.filelist}
    if EXPORT_XML not in filenames:
        raise click.ClickException("Zip file does not contain {}".format(EXPORT_XML))
    fp = zf.open(EXPORT_XML)
    db = sqlite_utils.Database(db_path)
    convert_xml_to_sqlite(fp, db)
