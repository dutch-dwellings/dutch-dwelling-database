import os

from psycopg2 import sql
from psycopg2.errors import UndefinedFile

from database_utils import create_table, get_connection
from file_utils import data_dir

FILENAME = 'WoON2018energie_e_1.0.csv'
TABLE_NAME = 'woon_2018_energie'
path = os.path.join(data_dir, FILENAME)

load_statement = sql.SQL("COPY {table_name} FROM %s WITH DELIMITER AS ';' NULL AS ' ' CSV HEADER;")

def sanitize_column_name(column_name):
	# TODO: anything else? Maybe make this a general
	# database util.
	# First row start with a 'FEFF' non breaking zero-width space
	# (WHY?!)
	return column_name.replace('\ufeff', '').replace('.', '_')

def alter_column_to_number(cursor, column_name):
	alter_statement = sql.SQL("ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE double precision USING replace({column_name}, ',','.')::double precision").format(
		table_name=sql.Identifier(TABLE_NAME),
		column_name=sql.Identifier(column_name))
	cursor.execute(alter_statement)

def main():
	try:
		with open(path, 'r') as file:
			header = file.readline().strip()
			column_names = header.split(';')
	except FileNotFoundError:
		print(f"Error: WoON survey data file not found.\nExpected file at {path}.")
		return

	columns = [(sanitize_column_name(column_name), 'text') for column_name in column_names]

	print('Creating table...')
	create_table(TABLE_NAME, columns)

	connection = get_connection()
	cursor = connection.cursor()
	# TODO: make this idempotent somehow?
	statement = load_statement.format(table_name=sql.Identifier(TABLE_NAME))
	try:
		print("Loading WoON survey data...")
		cursor.execute(statement, (path,))

	except UndefinedFile:
		print(f"Error: WoON survey data file not found.\nExpected file at {path}.")

	columns_to_alter = ['ew_huis', 'ew_pers']
	for column in columns_to_alter:
		alter_column_to_number(cursor, column)

	print("Committing...")
	cursor.close()
	connection.commit()
	connection.close()
	print("Done.")


if __name__ == '__main__':
	main()
