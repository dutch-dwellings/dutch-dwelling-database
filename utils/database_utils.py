from dotenv import dotenv_values
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT, AsIs
from psycopg2.extras import DictCursor

env = dotenv_values(".env")

def get_connection(dbname=env['POSTGRES_DBNAME']):
	return psycopg2.connect(
		dbname=dbname,
		user=env['POSTGRES_USER'],
		password=env['POSTGRES_PASSWORD']
	)

def get_cursor():
	connection = get_connection()
	return connection.cursor()

def create_database(dbname=env['POSTGRES_DBNAME']):

	create_statement = sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname))

	# Since every connection in Postgres has to be to a
	# specific database, we connect to the default
	# 'postgres' database in order to be able to make
	# a new database.
	connection = get_connection(dbname='postgres')
	# Autocommit is required since database creation
	# cannot run inside a transaction block.
	connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

	cursor = connection.cursor()
	# Database may already exist: this will throw
	# an error. We catch it so we get idempotency.
	try:
		cursor.execute(create_statement)
	except psycopg2.errors.DuplicateDatabase:
		pass
	cursor.close()
	connection.close()

def execute_file(path):

	connection = get_connection()
	cursor = connection.cursor()

	with open(path, 'r') as file:
		cursor.execute(file.read())

	cursor.close()
	connection.commit()
	connection.close()

def add_column(table_name, column_name, data_type, connection):
	cursor = connection.cursor()
	alter_statement = sql.SQL('ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} %s')
	alter_statement = alter_statement.format(
		table_name=sql.Identifier(table_name),
		column_name=sql.Identifier(column_name)
	)
	# We have to pass the data type 'AsIs',
	# because we cannot pass data_type as a sql Identifier,
	# since not all data types are valid when double quoted.
	# E.g. "int" or "integer" won't work. Maybe this is a bug
	# in PostgreSQL, because e.g. "varchar" does work.
	cursor.execute(alter_statement, (AsIs(data_type),))

def get_bag_sample(connection):
	'''
	Get a sample of 1000 random entries from the BAG table.
	'''
	cursor = connection.cursor(cursor_factory=DictCursor)
	query = "SELECT * FROM bag WHERE random() < 0.001 LIMIT 1000"
	cursor.execute(query)
	sample = cursor.fetchall()
	cursor.close()
	return sample

def insert_dict(table_name, row_dict, cursor):
	# implementation adapted from
	# https://stackoverflow.com/a/29471241/7770056

	columns = row_dict.keys()
	values = list(row_dict.values())

	# We cannot insert an empty dict into the database.
	if len(columns) == 0:
		return

	insert_statement = sql.SQL('INSERT INTO {table_name} (%s) VALUES %s').format(
		table_name = sql.Identifier(table_name)
	)

	cursor.execute(insert_statement, (AsIs(', '.join(columns)), tuple(values)))
