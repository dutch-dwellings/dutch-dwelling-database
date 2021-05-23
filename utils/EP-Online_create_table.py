import os

from database_utils import get_connection

FILENAME = 'EP-Online_create_table.sql'

folder = os.path.dirname(os.path.realpath(__file__))
path = os.path.join(folder, FILENAME)

connection = get_connection()
cursor = connection.cursor()

with open(path, 'r') as file:
	# print(file.read())
	cursor.execute(file.read())

connection.commit()
