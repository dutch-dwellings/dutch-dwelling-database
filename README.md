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
pip install python-dotenv psycopg2-binary requests scipy
```

## Downloading and loading the datasets

**First:** fill `.env` with the required values (see `.env.template` for the structure). You can get the required EP-Online API key with [this form from the RVO](https://epbdwebservices.rvo.nl/).

### Get required datasets

We try to automatically download as many datasets as possible, but some you still need to put into `data` manually:

- WoON survey: `WoON2018energie_e_1.0.csv`
- BAG (custom export enriched with dwelling types): `BAG_Invoer_RuimtelijkeData_BAG_vbo_woonfunctie_studiegebied_Export.csv`
- CBS:
	- [Kerncijfers PC6 2017 (`CBS-PC6-2017-v3.zip`)](https://download.cbs.nl/postcode/CBS-PC6-2017-v3.zip) ([info](https://www.cbs.nl/nl-nl/dossier/nederland-regionaal/geografische-data/gegevens-per-postcode)), extract `CBS_PC6_2017_v3.csv` from the ZIP archive
	- [Energiecijfers PC6 2019](https://www.cbs.nl/-/media/_excel/2020/33/energiecijfers_postcode6.zip) ([info](https://www.cbs.nl/nl-nl/maatwerk/2020/33/energielevering-aan-woningen-en-bedrijven-naar-postcode)) extract `Publicatiefile_Energie_postcode6_2019.csv` from the ZIP archive

### Loading
To download the rest of the data sets and load all of them, run the setup tool:

```
python setup.py
```

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

There are some unittests to test parts of the behaviour of the modules and the utils. They do not rely on the database, so you can run these without having PostgreSQL installed or the databases loaded.

To run all tests:

```
python -m unittest -v
```
