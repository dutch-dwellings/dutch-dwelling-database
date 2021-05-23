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

**First:** fill `.env` with the required values (see `.env.template` for the structure).

Then run the setup tool:

```
python setup.py
```

You will have to confirm a time/space/internet-consuming activity once in a while by typing `y` and then pressing Enter.

## TODO

- check if there energycertificates that have multiple BagPandIds (e.g. did I miss something when parsing the XML, or does every certicate have only one PandId?)
- make an option to have setup.py run without any input (and possibly without output, the UNIX-way)
