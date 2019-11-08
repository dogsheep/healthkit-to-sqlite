import click
import os
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
@click.option("-s", "--silent", is_flag=True, help="Don't show progress bar")
@click.option("--xml", is_flag=True, help="Input is XML, not a zip file")
def cli(export_zip, db_path, silent, xml):
    "Convert HealthKit file from exported zip file into a SQLite database"
    zf = None
    if xml:
        fp = open(export_zip, "r")
        file_length = os.path.getsize(export_zip)
    else:
        try:
            zf = zipfile.ZipFile(export_zip)
        except zipfile.BadZipFile:
            raise click.ClickException(
                "File is not a zip file. Use --xml if you are running against an XML file."
            )
        # Ensure export.xml is in there
        filenames = {zi.filename for zi in zf.filelist}
        if EXPORT_XML not in filenames:
            raise click.ClickException(
                "Zip file does not contain {}".format(EXPORT_XML)
            )
        fp = zf.open(EXPORT_XML)
        file_length = zf.getinfo("apple_health_export/export.xml").file_size
    db = sqlite_utils.Database(db_path)
    if silent:
        convert_xml_to_sqlite(fp, db, zipfile=zf)
    else:
        with click.progressbar(
            length=file_length, label="Importing from HealthKit"
        ) as bar:
            convert_xml_to_sqlite(fp, db, progress_callback=bar.update, zipfile=zf)
