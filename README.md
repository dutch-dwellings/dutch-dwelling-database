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

## Running the date pipeline

To run the data pipeline and populate the `results` table, first make sure that all required datasets have been loaded via the setup command above. Then:

```
python pipeline.py
```

Currently, this only uses a small sample of the BAG, for testing purposes.

## TODO

- check if there energycertificates that have multiple BagPandIds (e.g. did I miss something when parsing the XML, or does every certicate have only one PandId?)
- make an option to have setup.py run without any input (and possibly without output, the UNIX-way)
- make setup.py run idempotently. Make sure that datasets won't be loaded into PostgreSQL multiple times.
- take table names used in the creation of tables from .env
- normalize the database tables, and improve naming
