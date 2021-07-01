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
pip install python-dotenv psycopg2-binary requests cbsodata numpy pandas
```

For the analysis you might also need:

```
pip install scipy matplotlib scikit-learn seaborn statsmodels
```

And for mapping purposes:

```
pip install pyproj==2.5.0 folium
```

We use pyproj 2.5.0 since there is [some kind of bug](https://stackoverflow.com/questions/64713759/how-to-install-geopandas-properly#comment114426803_64713759) with more recent version.

## Downloading and loading the datasets

**First:** fill `.env` with the required values (see `.env.template` for the structure). You can get the required EP-Online API key with [this form from the RVO](https://epbdwebservices.rvo.nl/).

### Get required datasets

We try to automatically download as many datasets as possible. Only the BAG cannot be downloaded easily, so for that you will need to manually copy the file into the `data` folder:

- BAG (custom export enriched with dwelling types): `BAG_Invoer_RuimtelijkeData_BAG_vbo_woonfunctie_studiegebied_Export.csv`

If you want to do analysis on the WoON survey, you also need to copy the WoON results to `data`, but it is not required for the pipeline:

- WoON survey: `WoON2018energie_e_1.0.csv`

### Loading
To download the rest of the data sets and load all of them, make sure that you are connected to the internet and run the setup tool:

```
python setup.py
```

The setup tool should work idempotently: running it twice has the same effect of running it once (except when there are datasets missing in the first run of course). This means you can run it as often as you like (even though that should have no effect).

### CBS datasets

To manually download extra CBS-datasets for evaluation / exploration, get their table ID (e.g. from the [CBS Open Data Portal](https://opendata.cbs.nl/portal.html), find the 'Identifier' that is usually of the form '12345NED') and then:

```
python utils/CBS_load_tables.py $tableID
```

If these datasets are required for the pipeline to run, make sure to include them in the `cbs()` function within `setup.py` so that they will be downloaded during the setup.

## Running the date pipeline

To run the data pipeline and populate the `results` table, first make sure that all required datasets have been loaded via the setup command above. Then:

```
python pipeline.py
```

This will run the pipeline on the whole BAG (~8M entries), so it can take while (up to a day or so). To process only a subset, use either the flags `--N <N>` to limit processing to N dwellings or `--vbo_id <vbo_id>` to process one specific dwelling and its neighbourhood.

Results from previous runs are saved; new runs automatically exclude dwellings that have already been processed.
To force a fresh run and delete all previous results, use the `--fresh` flag.

## Tests

There are some unittests to test parts of the behaviour of the modules and the utils. They do not rely on the database, so you can run these without having PostgreSQL installed or the databases loaded.

To run all tests:

```
python -m unittest [-v]
```
