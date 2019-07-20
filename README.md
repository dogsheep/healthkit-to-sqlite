# healthkit-to-sqlite

[![PyPI](https://img.shields.io/pypi/v/healthkit-to-sqlite.svg)](https://pypi.org/project/healthkit-to-sqlite/)
[![CircleCI](https://circleci.com/gh/dogsheep/healthkit-to-sqlite.svg?style=svg)](https://circleci.com/gh/dogsheep/healthkit-to-sqlite)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/dogsheep/healthkit-to-sqlite/blob/master/LICENSE)

Convert an Apple Healthkit export zip to a SQLite database

## How to install

    $ pip install healthkit-to-sqlite

## How to use

First you need to export your Apple HealthKit data.

1. On your iPhone, open the "Health" app
2. Click the profile icon in the top right
3. Click "Export Health Data" at the bottom of that page
4. Save the resulting file somewhere you can access it on a laptop - I used Dropbox

Now you can convert the resulting `export.zip` file to SQLite like so:

    $ healthkit-to-sqlite export.zip healthkit.db

You can explore the resulting data using [Datasette](https://datasette.readthedocs.io/) like this:

    $ datasette healthkit.db
