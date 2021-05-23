import os
import sys

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from database_utils import get_connection

CREATE_TABLE_SQL = 'EP_Online_create_table.sql'

def create_energy_labels_table():

	folder = os.path.dirname(os.path.realpath(__file__))
	path = os.path.join(folder, CREATE_TABLE_SQL)

	connection = get_connection()
	cursor = connection.cursor()

	with open(path, 'r') as file:
		cursor.execute(file.read())

	cursor.close()
	connection.commit()
	connection.close()

if __name__ == "__main__":
	create_energy_labels_table()
