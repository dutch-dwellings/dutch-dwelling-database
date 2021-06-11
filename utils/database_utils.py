import os
import sys

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT, AsIs
from psycopg2.extras import DictCursor
from psycopg2.errors import InvalidTableDefinition, UndefinedColumn

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from utils.file_utils import get_env

env = get_env()

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

def get_bag_sample(connection, n=1000):
	'''
	Get a sample of random entries (default: 1000 entries)
	from the BAG table. Note: might return a little fewer entries
	than requested.
	'''
	# Determines how far into the database we go look for entries.
	# With speed_up = 1, we query roughly the entire database before the
	# LIMIT is reached, and the sample is more or less representative.
	# But we can save time by limiting the query to the first 1 / speed_up
	# part of the database.
	speed_up = 5
	# Estimate of total rows in the BAG database, doesn't need to be precise.
	n_rows = 7951730
	# Estimate of required random share of rows to be selected
	# in order to gather 'n' entries, increased by the speed_up
	required_share = n / n_rows * speed_up

	cursor = connection.cursor(cursor_factory=DictCursor)
	query = "SELECT * FROM bag WHERE random() < %s LIMIT %s"
	cursor.execute(query, (required_share, n))
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

def create_table(table_name, columns):
	'''
	Create a new table (will not create if table
	already exists) with name 'table_name',
	and columns defined in a list with tuples
	(column_name, data_type).
	E.g.
		columns = [('id', 'int'), ('neighbourhood', 'character varying')]
	'''
	connection = get_connection()
	cursor = connection.cursor()

	# use IF NOT EXISTS to make the statement idempotent
	create_statement = sql.SQL("CREATE TABLE IF NOT EXISTS {table_name} (%s);").format(
		table_name=sql.Identifier(table_name),
		# columns=sql.Identifier(columns_sql)
		)

	# TODO: check whether we can do this more
	# elegantly using e.g. psycopg2.sql
	columns_sql = ', '.join([' '.join(column) for column in columns])

	cursor.execute(create_statement, (AsIs(columns_sql),))
	cursor.close()
	connection.commit()
	connection.close()

def add_index(table_name, column_name):
	'''
	Create index on 'column_name' in
	'table_name'. Check whether index already
	exists to make it idempotent.
	'''
	index_name = f'{column_name}_idx'
	statement = sql.SQL("CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({column_name})").format(
			index_name = sql.Identifier(index_name),
			table_name = sql.Identifier(table_name),
			column_name = sql.Identifier(column_name)
		)
	connection = get_connection()
	cursor = connection.cursor()
	cursor.execute(statement)
	cursor.close()
	connection.commit()
	connection.close()

def make_primary_key(table_name, column_name):
	'''
	Make 'column_name' the primary key for 'table_name',
	if no primary key has yet been set.
	'''
	statement = sql.SQL("ALTER TABLE {table_name} ADD PRIMARY KEY ({column_name})").format(
			table_name = sql.Identifier(table_name),
			column_name = sql.Identifier(column_name)
		)
	connection = get_connection()
	cursor = connection.cursor()

	try:
		cursor.execute(statement)
	# Happens when we already added a primary key,
	# so we catch it and do nothing, makes it idempotent.
	except InvalidTableDefinition as e:
		print(f"Table '{table_name}' already has primary key on column '{column_name}'")

	cursor.close()
	connection.commit()
	connection.close()

def table_exists(table_name, dbname=env['POSTGRES_DBNAME']):
	'''
	Check whether a table with name 'table_name' exists.
	Return True or False.
	'''
	# Adapted from https://stackoverflow.com/a/1874268/7770056
	query = "SELECT exists(SELECT * FROM information_schema.tables WHERE table_catalog = %s AND table_name = %s)"

	connection = get_connection()
	cursor = connection.cursor()
	cursor.execute(query, (dbname, table_name))
	result = cursor.fetchone()[0]
	connection.close()
	return result

def table_empty(table_name):
	'''
	Check whether the table with name 'table_name' is empty.
	Assumes the table exists. Return True or False.
	'''
	query = sql.SQL("SELECT COUNT(*) FROM (SELECT * FROM {table_name} LIMIT 1) sq").format(
		table_name=sql.Identifier(table_name))
	connection = get_connection()
	cursor = connection.cursor()
	cursor.execute(query)
	result = cursor.fetchone()[0]
	if result == 1:
		return False
	else:
		return True

def execute(statement):
	connection = get_connection()
	cursor = connection.cursor()
	try:
		cursor.execute(statement)
	except Exception as e:
		raise(e)
	# Even when an error is raised during execution,
	# we need to clean up the cursor and connection.
	finally:
		cursor.close()
		connection.commit()
		connection.close()

def rename_column(table_name, col_name, new_col_name):
	statement = sql.SQL("ALTER TABLE {table_name} RENAME COLUMN {col_name} TO {new_col_name}").format(
		table_name=sql.Identifier(table_name),
		col_name=sql.Identifier(col_name),
		new_col_name=sql.Identifier(new_col_name)
	)
	try:
		execute(statement)
	except UndefinedColumn:
		print(f'Did not rename column {col_name} to {new_col_name} since it does not exist.')
