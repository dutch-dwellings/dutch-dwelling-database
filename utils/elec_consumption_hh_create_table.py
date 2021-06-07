import os
import sys

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from database_utils import execute_file

CREATE_TABLE_SQL = 'elec_consumption_hh_create_table.sql'

def main():
	folder = os.path.dirname(os.path.realpath(__file__))
	path = os.path.join(folder, CREATE_TABLE_SQL)
	execute_file(path)

if __name__ == "__main__":
	main()
