import os
import sys

from psycopg2.errors import UndefinedFile
from psycopg2 import sql

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from database_utils import get_connection
from file_utils import data_dir


FILE_NAME = 'BAG_Invoer_RuimtelijkeData_BAG_vbo_woonfunctie_studiegebied_Export.csv'
TABLE_NAME = 'bag'

# note: '''' means: use the character ' as quote character.
# It is escaped by the preceding ' and then included in ' ', hence the 4 ''''.
load_statement = sql.SQL("COPY {dbname} FROM %s WITH DELIMITER AS ';' NULL AS 'null' QUOTE '''' CSV HEADER;")


def main():
	path = os.path.join(data_dir, FILE_NAME)
	statement = load_statement.format(dbname=sql.Identifier(TABLE_NAME))

	connection = get_connection()
	cursor = connection.cursor()

	try:
		print("Loading BAG records, this might take a minute or so.")
		cursor.execute(statement, (path,))
		cursor.close()
		connection.commit()
		connection.close()
		print("Done.")
	except UndefinedFile:
		print(f"\nError: BAG data file not found.\nExpected file at {path}.")

if __name__ == "__main__":
	main()