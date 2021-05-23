# Dutch Dwelling Database
*A database of energy characteristics of individual Dutch dwellings*


### Installation

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

## Datasets

First: fill `.env` with the required values (see `.env.template` for the structure).

### Energy labels (EP-Online)

Make sure that a valid API-key is present in `.env` (available from the [RVO-site](https://epbdwebservices.rvo.nl/)).

Download the dataset, create the table in Postgres and load in the data ():

```
python utils/EP-Online_download_XML.py
python utils/EP-Online_create_table.py
python utils/EP-Online_load_XML.py
```

**Warning:** downloading the XML uses quite some disk space – roughly 4GB. Loading the dataset can take a while - roughly 15min. The scripts should warn you for this.

**Note:** development started with the CSV file (see files `EP-Online_(down)load_CSV.py`), but that isn't reliable since it uses `;` as a delimiter but also has values that contain `;`, messing up the parsing. Therefore we have to use the bulkier XML.