from dotenv import dotenv_values
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

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
