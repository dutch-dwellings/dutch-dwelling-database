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

# The municipality of Amsterdam has the annoying habit of using 1005 as the
# default value for buildings that are old but have no known building year:
# https://www.amsterdam.nl/stelselpedia/bag-index/baten-bag/afleiden-bouwjaren/
# There are quite a lot of them, last we checked 18043 entries.
# They are probably built before 1800 though:
# "Amsterdam gebruikt dummywaarde 1005 voor objecten die nog niet exact
# gedateerd zijn, maar wel voor 1800 liggen."
# https://www.cbs.nl/-/media/cbs%20op%20maat/microdatabestanden/documents/2019/29/levcyclwoonnietwoonbus.pdf
# We set them to 1800 because it doesn't really matter much for us given that age,
# and 1800 is probably more accurate than 1005. We could have also set it to NULL
# but 1800 is more insightful, even when wrong.
update_statement = "UPDATE bag SET bouwjaar = 1800 WHERE bouwjaar = 1005"

def main():
	path = os.path.join(data_dir, FILE_NAME)
	statement = load_statement.format(dbname=sql.Identifier(TABLE_NAME))

	connection = get_connection()
	cursor = connection.cursor()

	try:
		print("Loading BAG records, this might take a minute or so.")
		cursor.execute(statement, (path,))
		cursor.execute(update_statement)
		cursor.close()
		connection.commit()
		connection.close()
		print("Done.")
	except UndefinedFile:
		print(f"\nError: BAG data file not found.\nExpected file at {path}.")

if __name__ == "__main__":
	main()
