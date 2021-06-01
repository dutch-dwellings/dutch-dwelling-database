# Dutch Dwelling Database
*A database of energy characteristics of individual Dutch dwellings*


## Installation

Make sure you have Python3 and [PostgreSQL](https://www.postgresql.org/download/) installed. On macOS you can use [Homebrew](https://brew.sh/):
`brew install postgresql`, or use the [PostgreSQL installer](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads).

Make sure that `psql` is accessible in your terminal. If you used the installer on macOS you might need to [update your `PATH`](https://dba.stackexchange.com/a/3008) with e.g. `/Library/PostgreSQL/12/bin/`.


To check installed versions (any later versions will probably work too):

```
$ python --version
Python 3.7.5
$ psql --version
psql (PostgreSQL) 12.6
```

### Install Python dependencies

```
pip install python-dotenv psycopg2-binary requests
```

## Downloading and loading the datasets

**First:** fill `.env` with the required values (see `.env.template` for the structure). You can get the required EP-Online API key with [this form from the RVO](https://epbdwebservices.rvo.nl/).

To download and load all the datasets, run the setup tool:

```
python setup.py
```

You will have to confirm a time/space/internet-consuming activity once in a while by typing `y` and then pressing Enter.

### CBS datasets

To manually download extra CBS-datasets for evaluation / exploration, get their table ID (e.g. from the [CBS Open Data Portal](https://opendata.cbs.nl/portal.html), find the 'Identifier' that is usually of the form '12345NED') and then:

```
python utils/CBS_load_tables.py $tableID
```

If these datasets are required for the pipeline to run, make sure to include them in the `cbs()` function within `setup.py` so these will download during the setup.

## Running the date pipeline

To run the data pipeline and populate the `results` table, first make sure that all required datasets have been loaded via the setup command above. Then:

```
python pipeline.py
```

Currently, this only uses a small sample of the BAG, for testing purposes.

## Tests

There are unittests for the behaviour of the modules. They do not rely on the database, so you can run these without having PostgreSQL installed or the databases loaded.

To run all tests:

```
python -m unittest -v
```

## TODO

- check if there energycertificates that have multiple BagPandIds (e.g. did I miss something when parsing the XML, or does every certicate have only one PandId?)
- make an option to have setup.py run without any input (and possibly without output, the UNIX-way)
- make setup.py run idempotently. Make sure that datasets won't be loaded into PostgreSQL multiple times.
- take table names used in the creation of tables from .env
- normalize the database tables, and improve naming
- `utils/CBS_utils`:
	- speed up insertion by bundling INSERT statements. Probably need to build some kind of 'insert buffer' for this.
- `utils/EP_Online_download`:
	- consider deleting the ZIP file after unzipping (but might be useful to prevent re-downloading)
	- give a warning before unzipping the file that it can take quite a lot of disk space
	- return filename to be used later on
