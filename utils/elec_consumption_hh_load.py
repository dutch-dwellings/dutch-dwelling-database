import os
import sys

from psycopg2.errors import UndefinedFile
from psycopg2 import sql

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from database_utils import get_connection
from file_utils import data_dir

FILE_NAME = 'elec_consumption_no heating.csv'
TABLE_NAME = 'elec_consumption_households'

load_statement = sql.SQL("COPY {dbname} FROM %s WITH DELIMITER AS ',' CSV HEADER;")

def main():
	path = os.path.join(data_dir, FILE_NAME)
	statement = load_statement.format(dbname=sql.Identifier(TABLE_NAME))

	connection = get_connection()
	cursor = connection.cursor()

	try:
		print("Loading household consumption records")
		cursor.execute(statement, (path,))
	except UndefinedFile:
		print(f"\nError: household consumption data file not found.\nExpected file at {path}.")

	cursor.close()
	connection.commit()
	connection.close()

if __name__ == "__main__":
	main()
