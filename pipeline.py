from psycopg2 import sql

from utils.database_utils import get_connection, get_bag_sample, insert_dict
from utils.create_results_table import main as create_results_table
from modules.district_heating_module import DistrictHeatingModule


class Dwelling:

	def __init__(self, attributes):
		self.attributes = attributes
		# We copy the list so we get an instance variable
		# instead of a class variable.
		self.outputs = self.default_outputs.copy()

	def get_filtered_attributes(self):
		'''
		Get the attributes and their values
		that need to be output to the database.
		'''
		return {key: val for (key, val) in self.attributes.items() if key in self.outputs}

	def save(self, connection):
		'''
		INSERT the generated Dwelling object
		into the 'results' database.
		'''
		cursor = connection.cursor()

		row_dict = self.get_filtered_attributes()
		insert_dict(
			table_name='results',
			row_dict = row_dict,
			cursor = cursor
		)

		cursor.close()

	# This defines the default outputs irrespective of which
	# modules are active. Specify the outputs for specific modules
	# within the class definition of that module.
	#
	# This has to match the default 'results'
	# table layout as defined in utils/create_results_table.sql.
	# In other words: columns have to exist for all the
	# default_outputs.
	#
	# As of now, we can only assume that BAG-data is always present,
	# so only use BAG column_names here.
	default_outputs = ['identificatie']


def main():

	connection = get_connection()
	create_results_table()
	sample = get_bag_sample(connection)
	district_heating_module = DistrictHeatingModule(connection)

	for entry in sample:
		dwelling = Dwelling(dict(entry))
		district_heating_module.process(dwelling)
		dwelling.save(connection)

	connection.commit()
	connection.close()

if __name__ == "__main__":
	main()
