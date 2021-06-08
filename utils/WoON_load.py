import os

from psycopg2 import  sql

from database_utils import create_table, get_connection
from file_utils import data_dir

FILENAME = 'WoON2018energie_e_1.0.csv'
TABLE_NAME = 'woon_2018_energie'
path = os.path.join(data_dir, FILENAME)

load_statement = sql.SQL("COPY {table_name} FROM %s WITH DELIMITER AS ';' NULL AS ' ' CSV HEADER;")

def sanitize_column_name(column_name):
	# TODO: anything else? Maybe make this a general
	# database util.
	return column_name.replace('.', '_')

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
		print("Committing...")
		cursor.close()
		connection.commit()
		connection.close()
		print("Done.")
	except UndefinedFile:
		print(f"Error: WoON survey data file not found.\nExpected file at {path}.")

if __name__ == '__main__':
	main()